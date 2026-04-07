import json
import random
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import matplotlib.pyplot as plt
import seaborn as sns
from IPython.display import clear_output, display

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
import fdb
from datetime import timedelta, datetime

# %%

# Конфигурация проекта (создается автоматически при первом запуске)
def _resolve_existing_runtime_path(path_value):
    """Resolve existing file path for normal/python and PyInstaller modes."""
    candidate = Path(path_value)
    if candidate.exists():
        return candidate
    if candidate.is_absolute():
        return candidate
    bundle_dir = getattr(sys, "_MEIPASS", None)
    if bundle_dir:
        bundled_candidate = Path(bundle_dir) / candidate
        if bundled_candidate.exists():
            return bundled_candidate
    return candidate


config_path = _resolve_existing_runtime_path('config.json')
default_config = {
    "_comment": "Настройки проекта. Комментарии хранятся в полях с префиксом _comment_.",
    "database": {
        "_comment_dsn": "DSN Firebird в формате HOST:PATH_TO_FDB",
        "dsn": "10.15.2.58:D:\\SA2024.FDB",
        "_comment_user": "Пользователь БД",
        "user": "SYSDBA",
        "_comment_password": "Пароль БД",
        "password": "masterkey"
    },
    "model": {
        "_comment_input_dim": "Размер входного вектора сети (используется в synthetic_data)",
        "input_dim": 3996,
        "_comment_output_dim": "Размер выходного вектора сети (используется в synthetic_data)",
        "output_dim": 228,
        "_comment_hidden_dims": "Размеры скрытых слоев MLP",
        "hidden_dims": [1024, 512, 256],
        "_comment_dropout": "Dropout для скрытых слоев",
        "dropout": 0.3,
        "_comment_use_genetic_search": "Включить генетический подбор топологии hidden_dims",
        "use_genetic_search": False
    },
    "genetic_search": {
        "_comment_population_size": "Размер популяции",
        "population_size": 10,
        "_comment_generations": "Количество поколений",
        "generations": 5,
        "_comment_survivors": "Сколько лучших особей оставлять в поколении",
        "survivors": 4,
        "_comment_mutation_rate": "Вероятность мутации (0..1)",
        "mutation_rate": 0.35,
        "_comment_min_layers": "Минимум скрытых слоев",
        "min_layers": 1,
        "_comment_max_layers": "Максимум скрытых слоев",
        "max_layers": 4,
        "_comment_min_units": "Минимум нейронов в слое",
        "min_units": 64,
        "_comment_max_units": "Максимум нейронов в слое",
        "max_units": 1024,
        "_comment_units_step": "Шаг по количеству нейронов",
        "units_step": 64,
        "_comment_eval_epochs": "Эпох для быстрой оценки одной топологии",
        "eval_epochs": 3
    },
    "training": {
        "_comment_learning_rate": "Скорость обучения оптимизатора Adam",
        "learning_rate": 0.001,
        "_comment_num_epochs": "Максимальное количество эпох обучения",
        "num_epochs": 100,
        "_comment_batch_size": "Размер батча",
        "batch_size": 12,
        "_comment_train_split": "Доля обучающей выборки (0..1)",
        "train_split": 0.8,
        "_comment_use_early_stopping": "Остановить обучение при отсутствии улучшения",
        "use_early_stopping": True,
        "_comment_early_stopping_patience": "Сколько эпох ждать улучшения",
        "early_stopping_patience": 12,
        "_comment_early_stopping_min_delta": "Минимальное улучшение val_loss, чтобы считать прогресс",
        "early_stopping_min_delta": 0.0001,
        "_comment_checkpoint_path": "Путь к файлу чекпоинта модели",
        "checkpoint_path": "mlp_checkpoint.pt",
        "_comment_resume_from_checkpoint": "Дообучать из checkpoint_path, если файл существует",
        "resume_from_checkpoint": True
    },
    "synthetic_data": {
        "_comment_enabled_on_empty_db": "Генерировать тестовые данные при пустом результате БД",
        "enabled_on_empty_db": True,
        "_comment_samples": "Количество синтетических примеров",
        "samples": 256,
        "_comment_dims_source": "Размерности synthetic данных берутся из model.input_dim/model.output_dim",
        "dims_source": "model",
        "_comment_noise_std": "Стандартное отклонение шума в целевой переменной",
        "noise_std": 0.05,
        "_comment_seed": "Seed для воспроизводимости генерации",
        "seed": 42
    }
}

def merge_defaults(user_cfg, default_cfg):
    if not isinstance(user_cfg, dict):
        return default_cfg
    merged = dict(user_cfg)
    for key, value in default_cfg.items():
        if key not in merged:
            merged[key] = value
        elif isinstance(value, dict):
            merged[key] = merge_defaults(merged[key], value)
    return merged

cfg = default_config
if not config_path.exists():
    config_path.write_text(json.dumps(default_config, indent=2, ensure_ascii=False), encoding='utf-8')
    print(f'Файл конфигурации создан: {config_path.resolve()}')
else:
    try:
        cfg = json.loads(config_path.read_text(encoding='utf-8'))
        cfg = merge_defaults(cfg, default_config)
        config_path.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding='utf-8')
        print(f'Файл конфигурации загружен: {config_path.resolve()}')
    except Exception as e:
        print(f'Ошибка чтения config.json, используются значения по умолчанию: {e}')
        cfg = default_config
        config_path.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding='utf-8')

# Подключение к БД
db_cfg = cfg.get('database', {})
tp_con = None
tp_cur = None
try:
    tp_con = fdb.connect(
        dsn=db_cfg.get('dsn', default_config['database']['dsn']),
        user=db_cfg.get('user', default_config['database']['user']),
        password=db_cfg.get('password', default_config['database']['password'])
    )
    tp_cur = tp_con.cursor()
    print('Подключение к БД успешно')
except Exception as e:
    print(f'Ошибка подключения к БД: {e}')

# %%

# Функции для большой/малой картограмм
class TPoint:
    def __init__(self, X = 0, Y = 0):
        self.X = X
        self.Y = Y

def getCoordLine(Coord8, isBigCartogram):
    NA = [1,11,31,55,83,115,149,185,223,263,305,349,395,443,491,
			541,591,643,695,749,803,857,911,965,1021,1077,1133,1189,1245,1301,
			1357,1413,1469,1525,1579,1633,1687,1741,1795,1847,1899,1949,1999,
			2047,2095,2141,2185,2227,2267,2305,2341,2375,2407,2435,2459,2479,2489]
    NA1 = [1,15,35,59,87,117,149,183,219,257,297,339,381,425,469,
			515,561,607,655,703,751,799,847,895,943,991,1039,1087,1135,1183,
			1231,1279,1325,1371,1417,1461,1505,1547,1589,1629,1667,1703,1737,
			1769,1799,1827,1851,1871,1885]
    Error = False
    L = -1
    NY = Coord8.Y
    NX = Coord8.X
    if isBigCartogram:
        NY = 60 - NY + (NY // 10) * 2
        if (NY <= 0) or (NY >= 57):
            Error = True
        else:
            L = ((NA[NY-1]+NA[NY]) // 2)+NX-(NX // 10)*2-32
            if (L < NA[NY-1]) or (L >= NA[NY]) or (L<=0) or (L>2488):
                Error = True
    else:
        NY = 56-NY+(NY // 10)*2
        if (NY <= 0) or (NY >= 49):
            Error = True
        else:
            L = ((NA1[NY-1]+NA1[NY]) // 2)+NX-(NX // 10)*2-32
            if (L<NA1[NY-1]) or (L>=NA1[NY]) or (L<=0) or (L>1884):
                Error = True
    return L if not Error else -1

def getCoord8(CoordLine, isBigCartogram):
    I = 0
    J = 0
    IB = [24,19,17,15,13,12,11,10,9,8,7,6,5,5,4,4,3,3,
          2,2,2,2,2,1,1,1,1,1,1,1,1,1,1,2,2,2,2,2,3,3,4,
          4,5,5,6,7,8,9,10,11,12,13,15,17,19,24]
    IT = [-23,-8,14,40,70,103,138,175,214,255,298,343,
          390,438,487,537,588,640,693,747,801,855,909,964,
          1020,1076,1132,1188,1244,1300,1356,1412,1468,1523,
          1577,1631,1685,1739,1792,1844,1895,1945,1994,2042,
          2089,2134,2177,2218,2257,2294,2329,2362,2392,2418,2440,2455]
    IB1 = [22,19,17,15,14,13,12,11,10,9,8,8,7,7,6,
           6,6,5,5,5,5,5,5,5,5,5,5,5,5,5,5,6,6,6,7,7,8,8,
           9,10,11,12,13,14,15,17,19,22]
    IT1 = [-21,-4,18,44,73,104,137,172,209,248,289,
           331,374,418,463,509,555,602,650,698,746,794,842,890,
           938,986,1034,1082,1130,1178,1226,1273,1319,1365,1410,
           1454,1497,1539,1580,1619,1656,1691,1724,1755,1784,1810,1832,1849]

    result = TPoint(-1, -1)
    if isBigCartogram:
        for II in range(2, 57):
            I = II-1
            if (CoordLine<IB[II-1]+IT[II-1]):
                break
            I = II
        J = CoordLine-IT[I-1]
    else:
        for II in range(2, 49):
            I = II-1
            if (CoordLine<IB1[II-1]+IT1[II-1]):
                break
            I = II
        J = CoordLine - IT1[I-1]
        I = I+4
    
    I = 57-I
    result.Y = ((I+3) // 8)*2+I+3
    result.X = ((J+3) // 8)*2+J+3
    return result

def getLinBigToSmall(CoordLine):
    C8big = getCoord8(CoordLine, True)
    CoordLineSmall = getCoordLine(C8big, False)
    if(CoordLineSmall > 0):
        return getCoord8(CoordLineSmall)
    else:
        return TPoint(-1, -1)

def getC8SmallToBig(Coord8):
    return getCoord8(getCoordLine(Coord8, False), True)

bigcoords = [getC8SmallToBig(getCoord8(i, False)) for i in range(1884)]
bigcoord_id = [("0"+(str(p.X)) if p.X < 10 else str(p.X)) + (("0"+str(p.Y))if p.Y<10 else str(p.Y)) for p in bigcoords]
test_set = set(bigcoord_id)
len(test_set), len(bigcoord_id)

# %%

# Основной SQL-запрос
query = "SELECT \
  t.TADATE AS special_event_time, \
  t.COORD AS coord, \
  t.OLD_ENVYR - t.NEW_ENVYR AS envyr_change, \
  (SELECT FIRST 1 b.WTTK FROM CL b \
   WHERE b.TADATE <= DATEADD(HOUR, -1, t.TADATE) \
   ORDER BY b.TADATE DESC) AS wttk_blob, \
  (SELECT FIRST 1 c_before.CR FROM DA c_before \
   WHERE c_before.TADATE <= DATEADD(HOUR, -1, t.TADATE) \
   ORDER BY c_before.TADATE DESC) AS coord0_blob, \
  (SELECT FIRST 1 c_after.CR FROM DA c_after \
   WHERE c_after.TADATE >= DATEADD(HOUR, 1, t.TADATE) \
   ORDER BY c_after.TADATE ASC) AS coord1_blob \
FROM PEREGRUZ_LOG t \
WHERE t.OLD_TYPE < 3 AND t.NEW_TYPE < 3 AND t.OLD_TYPE = t.NEW_TYPE AND t.OLD_ENVYR - t.NEW_ENVYR > 2600"

res = []
if tp_cur is None:
    print('SQL-запрос пропущен: курсор БД не инициализирован')
else:
    try:
        tp_cur.execute(query)
        res = tp_cur.fetchall()
        print(f'Загружено строк из PEREGRUZ_LOG: {len(res)}')
    except Exception as e:
        print(f'Ошибка выполнения запроса к БД: {e}')

if not res:
    print('[WARN] Предупреждение: основной запрос к БД вернул 0 строк')

# %%

# Извлечение восьмеричных координат
coords = []
st = []
coord_id = None
st_id = None
coords_list = []
st_list = []

if tp_cur is None:
    print('Загрузка COORDS пропущена: курсор БД не инициализирован')
else:
    try:
        coord_query = "SELECT K8 FROM COORDS"
        tp_cur.execute(coord_query)
        coords = tp_cur.fetchall()

        st_query = "SELECT CR FROM COORDS"
        tp_cur.execute(st_query)
        st = tp_cur.fetchall()

        if not coords or not st:
            print('Таблица COORDS вернула пустые данные')
        else:
            idx = list(range(1884))
            coord_id = pd.Series(coords[0][0], index=idx)
            ids = list(range(228))
            st_id = pd.Series(st[0][0], index=ids)
            coords_list = [coord_id[i] for i in range(1884)]
            st_list = [st_id[i] for i in range(228)]
            print('Координаты из COORDS успешно загружены')
    except Exception as e:
        print(f'Ошибка чтения COORDS: {e}')

# %%

# Именованные столбцы таблиц БД для каждого отдельного канала
# X_column_names = ['envyr_change_ch' + str(coord_id[i]) for i in range(1884)] +\
#     ['wttk_ch' + str(coord_id[i]) for i in range(1884)] + ['old_coord_ch' + str(st_id[i]) for i in range(228)]
# Y_column_names = ['new_coord_ch' + str(st_id[i]) for i in range(228)]
# len(X_column_names)

# %%

# Составление общих таблиц входных и выходных данных сети
X = None
y = None
X_train = None
X_val = None
y_train = None
y_val = None
train_loader = None
val_loader = None

try:
    train_cfg = cfg.get('training', {}) if isinstance(cfg, dict) else {}
    synth_cfg = cfg.get('synthetic_data', {}) if isinstance(cfg, dict) else {}
    model_cfg = cfg.get('model', {}) if isinstance(cfg, dict) else {}

    train_split = float(train_cfg.get('train_split', 0.8))
    train_split = min(max(train_split, 0.1), 0.95)

    batch_size = int(train_cfg.get('batch_size', 12))
    if batch_size <= 0:
        batch_size = 12

    entries = len(res)
    has_db_data = entries > 0 and coord_id is not None and st_id is not None

    if has_db_data:
        # Входные данные из БД
        X = torch.tensor([[res[i][2] if res[i][1] == coord_id[j] else 0 for i in range(entries)] for j in range(1884)] +
                         [[res[i][3][j] for i in range(entries)] for j in range(1884)] +
                         [[res[i][4][j] for i in range(entries)] for j in range(228)],
                         dtype=torch.float32).T

        # Выходные величины из БД
        y = torch.tensor([[res[i][5][j] for i in range(entries)] for j in range(228)], dtype=torch.float32).T
    else:
        use_synth = bool(synth_cfg.get('enabled_on_empty_db', True))
        if not use_synth:
            print('Подготовка датасета пропущена: данных БД нет, генерация synthetic_data отключена')
        else:
            samples = int(synth_cfg.get('samples', 256))
            input_dim = int(model_cfg.get('input_dim', 3996))
            output_dim = int(model_cfg.get('output_dim', 228))
            noise_std = float(synth_cfg.get('noise_std', 0.05))
            seed = int(synth_cfg.get('seed', 42))

            samples = max(samples, 2)
            input_dim = max(input_dim, 1)
            output_dim = max(output_dim, 1)
            noise_std = max(noise_std, 0.0)

            gen = torch.Generator().manual_seed(seed)
            X = torch.randn(samples, input_dim, generator=gen, dtype=torch.float32)
            W = torch.randn(input_dim, output_dim, generator=gen, dtype=torch.float32)
            noise = noise_std * torch.randn(samples, output_dim, generator=gen, dtype=torch.float32)
            y = X @ W + noise
            print(f'[WARN] Предупреждение: данных из БД нет, сгенерирован synthetic dataset: samples={samples}, input_dim={input_dim}, output_dim={output_dim}')

    if X is not None and y is not None:
        # Нормализация данных: вычитаем среднее, делим на стандартное отклонение
        mean = X.mean(dim=0, keepdim=True)
        std = X.std(dim=0, keepdim=True, correction=0)
        X = (X - mean) / (std + 1e-8)

        n_samples = X.shape[0]
        if n_samples == 1:
            split = 1
        else:
            split = max(1, int(train_split * n_samples))
            if split >= n_samples:
                split = n_samples - 1

        X_train, X_val = X[:split], X[split:]
        y_train, y_val = y[:split], y[split:]

        train_dataset = TensorDataset(X_train, y_train)
        val_dataset = TensorDataset(X_val, y_val)

        train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
        val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)

        sns.set_theme(style='whitegrid')
        print(f'Датасет подготовлен: train={len(train_dataset)}, val={len(val_dataset)}')
except Exception as e:
    print(f'Ошибка подготовки датасета: {e}')

# %%

# Описание класса нейронной сети
# Простейшая многослойная сеть прямого распространения

class MLP(nn.Module):
    def __init__(self, input_dim, output_dim, hidden_dims=[1024, 512, 256], dropout=0.3):
        super().__init__()
        layers = []
        prev_dim = input_dim
        for hidden_dim in hidden_dims:
            layers.append(nn.Linear(prev_dim, hidden_dim))
            layers.append(nn.ReLU())
            layers.append(nn.Dropout(dropout))
            prev_dim = hidden_dim
        layers.append(nn.Linear(prev_dim, output_dim))
        self.network = nn.Sequential(*layers)

    def forward(self, x):
        return self.network(x)


def _safe_int(value, default):
    try:
        return int(value)
    except Exception:
        return default


def run_genetic_topology_search(X_train, y_train, X_val, y_val, base_dropout, base_lr, search_cfg):
    """Подбор hidden_dims генетическим алгоритмом по валидационному MSE."""
    population_size = max(4, _safe_int(search_cfg.get('population_size', 10), 10))
    generations = max(1, _safe_int(search_cfg.get('generations', 5), 5))
    survivors = max(2, _safe_int(search_cfg.get('survivors', 4), 4))
    mutation_rate = float(search_cfg.get('mutation_rate', 0.35))
    mutation_rate = min(max(mutation_rate, 0.0), 1.0)

    min_layers = max(1, _safe_int(search_cfg.get('min_layers', 1), 1))
    max_layers = max(min_layers, _safe_int(search_cfg.get('max_layers', 4), 4))
    min_units = max(8, _safe_int(search_cfg.get('min_units', 64), 64))
    max_units = max(min_units, _safe_int(search_cfg.get('max_units', 1024), 1024))
    units_step = max(1, _safe_int(search_cfg.get('units_step', 64), 64))
    eval_epochs = max(1, _safe_int(search_cfg.get('eval_epochs', 3), 3))

    unit_candidates = list(range(min_units, max_units + 1, units_step))
    if not unit_candidates:
        unit_candidates = [64, 128, 256]

    input_dim = X_train.shape[1]
    output_dim = y_train.shape[1]
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    def random_arch():
        layers_count = random.randint(min_layers, max_layers)
        return [random.choice(unit_candidates) for _ in range(layers_count)]

    def mutate_arch(arch):
        candidate = list(arch)
        if random.random() < mutation_rate and len(candidate) > min_layers:
            candidate.pop(random.randrange(len(candidate)))
        if random.random() < mutation_rate and len(candidate) < max_layers:
            candidate.insert(random.randrange(len(candidate) + 1), random.choice(unit_candidates))
        for i in range(len(candidate)):
            if random.random() < mutation_rate:
                candidate[i] = random.choice(unit_candidates)
        if len(candidate) < min_layers:
            candidate += [random.choice(unit_candidates) for _ in range(min_layers - len(candidate))]
        if len(candidate) > max_layers:
            candidate = candidate[:max_layers]
        return candidate

    def crossover(a, b):
        if not a:
            return b
        if not b:
            return a
        pivot_a = random.randint(1, len(a))
        pivot_b = random.randint(0, len(b) - 1)
        child = a[:pivot_a] + b[pivot_b:]
        if len(child) < min_layers:
            child += [random.choice(unit_candidates) for _ in range(min_layers - len(child))]
        if len(child) > max_layers:
            child = child[:max_layers]
        return child

    def evaluate_arch(hidden_dims):
        model_local = MLP(input_dim, output_dim, hidden_dims=hidden_dims, dropout=base_dropout).to(device)
        opt_local = optim.Adam(model_local.parameters(), lr=base_lr)
        crit_local = nn.MSELoss()

        model_local.train()
        for _ in range(eval_epochs):
            opt_local.zero_grad()
            pred = model_local(X_train.to(device))
            loss = crit_local(pred, y_train.to(device))
            loss.backward()
            opt_local.step()

        model_local.eval()
        with torch.no_grad():
            target_X = X_val if X_val is not None and X_val.shape[0] > 0 else X_train
            target_y = y_val if y_val is not None and y_val.shape[0] > 0 else y_train
            val_pred = model_local(target_X.to(device))
            val_loss = crit_local(val_pred, target_y.to(device)).item()
        return val_loss

    population = [random_arch() for _ in range(population_size)]
    best_arch = None
    best_loss = float('inf')
    best_gen = None
    ga_history = []

    for gen in range(generations):
        scored = []
        for arch in population:
            try:
                score = evaluate_arch(arch)
            except Exception:
                score = float('inf')
            scored.append((score, arch))

        scored.sort(key=lambda x: x[0])
        generation_best_loss = scored[0][0]
        generation_best_arch = list(scored[0][1])
        ga_history.append({
            'generation': gen + 1,
            'best_loss': generation_best_loss,
            'best_arch': generation_best_arch
        })

        if generation_best_loss < best_loss:
            best_loss = generation_best_loss
            best_arch = generation_best_arch
            best_gen = gen + 1

        layers_hist = {}
        for _, arch in scored:
            layers_hist[len(arch)] = layers_hist.get(len(arch), 0) + 1

        # Live-визуализация эволюции качества в процессе поиска
        clear_output(wait=True)
        ga_df_live = pd.DataFrame(ga_history)
        plt.figure(figsize=(8, 4))
        plt.plot(ga_df_live['generation'], ga_df_live['best_loss'], marker='o')
        plt.title('GA: лучший val_loss по поколениям (live)')
        plt.xlabel('Поколение')
        plt.ylabel('Best val_loss')
        plt.grid(True, alpha=0.3)
        plt.show()
        print(
            f'[LIVE] GA {gen+1}/{generations} | '
            f'gen_best_loss={generation_best_loss:.6f}, gen_best_arch={generation_best_arch} | '
            f'global_best_loss={best_loss:.6f}, global_best_arch={best_arch}, global_best_gen={best_gen} | '
            f'layers_dist={layers_hist}'
        )

        elite = [arch for _, arch in scored[:min(survivors, len(scored))]]
        next_population = elite.copy()

        # Поддерживаем разнообразие: добавляем случайного "иммигранта"
        if len(next_population) < population_size:
            next_population.append(random_arch())

        while len(next_population) < population_size:
            p1 = random.choice(elite)
            p2 = random.choice(elite)
            child = crossover(p1, p2)
            child = mutate_arch(child)

            # Повторяем мутацию, если ребенок совпал с родителем (чтобы архитектура реально менялась)
            attempts = 0
            while (child == p1 or child == p2) and attempts < 3:
                child = mutate_arch(child)
                attempts += 1

            next_population.append(child)
        population = next_population

    if best_arch is None:
        best_arch = [256, 128]
        best_gen = 1

    ga_df = pd.DataFrame(ga_history)
    if not ga_df.empty:
        print('\nИтог GA:')
        print(f'- Лучшее поколение: {best_gen}')
        print(f'- Лучшая топология (число слоёв = {len(best_arch)}): {best_arch}')
        print(f'- Лучший val_loss: {best_loss:.6f}')
        print('- История (первые/последние поколения):')
        summary_df = ga_df[['generation', 'best_loss', 'best_arch']].copy()
        display(pd.concat([summary_df.head(3), summary_df.tail(3)]))

    return best_arch, best_loss, ga_history

# %%

# Создание модели
model = None
criterion = None
optimizer = None
selected_hidden_dims = None
resume_epoch = 0
best_val_loss_resume = None
checkpoint_path = None
ga_history = []

try:
    if X_train is None or y_train is None:
        print('Создание модели пропущено: обучающие данные не готовы')
    else:
        model_cfg = cfg.get('model', {}) if isinstance(cfg, dict) else {}
        train_cfg = cfg.get('training', {}) if isinstance(cfg, dict) else {}
        ga_cfg = cfg.get('genetic_search', {}) if isinstance(cfg, dict) else {}

        input_size = X_train.shape[1]
        output_size = y_train.shape[1]
        hidden_dims = model_cfg.get('hidden_dims', [1024, 512, 256])
        dropout = float(model_cfg.get('dropout', 0.3))
        dropout = min(max(dropout, 0.0), 0.9)
        learning_rate = float(train_cfg.get('learning_rate', 0.001))
        if learning_rate <= 0:
            learning_rate = 0.001

        use_ga = bool(model_cfg.get('use_genetic_search', False))
        if use_ga:
            if X_train.shape[0] == 0:
                print('GA-подбор пропущен: пустой train')
            else:
                best_arch, best_loss, ga_history = run_genetic_topology_search(
                    X_train, y_train, X_val, y_val, dropout, learning_rate, ga_cfg
                )
                hidden_dims = best_arch
                print(f'GA-подбор завершен: hidden_dims={hidden_dims}, val_loss={best_loss:.6f}')

                if ga_history:
                    ga_df = pd.DataFrame(ga_history)
                    plt.figure(figsize=(8, 4))
                    plt.plot(ga_df['generation'], ga_df['best_loss'], marker='o')
                    plt.title('GA: лучший val_loss по поколениям')
                    plt.xlabel('Поколение')
                    plt.ylabel('Best val_loss')
                    plt.grid(True, alpha=0.3)
                    plt.show()

        selected_hidden_dims = hidden_dims
        model = MLP(input_size, output_size, hidden_dims=hidden_dims, dropout=dropout)
        criterion = nn.MSELoss()
        optimizer = optim.Adam(model.parameters(), lr=learning_rate)

        checkpoint_path = Path(train_cfg.get('checkpoint_path', 'mlp_checkpoint.pt'))
        checkpoint_load_path = _resolve_existing_runtime_path(checkpoint_path)
        resume_from_checkpoint = bool(train_cfg.get('resume_from_checkpoint', True))
        if resume_from_checkpoint and checkpoint_load_path.exists():
            try:
                checkpoint = torch.load(checkpoint_load_path, map_location='cpu')
                model.load_state_dict(checkpoint['model_state_dict'])
                optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
                resume_epoch = int(checkpoint.get('epoch', 0))
                best_val_loss_resume = checkpoint.get('best_val_loss', None)
                print(f'Чекпоинт загружен: {checkpoint_load_path}, epoch={resume_epoch}')
            except Exception as e:
                print(f'Не удалось загрузить чекпоинт, обучение с нуля: {e}')

        print(f'Модель создана: input={input_size}, output={output_size}, hidden_dims={hidden_dims}, lr={learning_rate}')
except Exception as e:
    print(f'Ошибка создания модели: {e}')

# %%

# Процесс обучения
train_cfg = cfg.get('training', {}) if isinstance(cfg, dict) else {}
num_epochs = int(train_cfg.get('num_epochs', 100))
if num_epochs <= 0:
    num_epochs = 100

use_early_stopping = bool(train_cfg.get('use_early_stopping', True))
early_stopping_patience = int(train_cfg.get('early_stopping_patience', 12))
if early_stopping_patience <= 0:
    early_stopping_patience = 12
early_stopping_min_delta = float(train_cfg.get('early_stopping_min_delta', 1e-4))
if early_stopping_min_delta < 0:
    early_stopping_min_delta = 1e-4

try:
    if model is None or criterion is None or optimizer is None:
        print('Обучение пропущено: модель не инициализирована')
    elif train_loader is None:
        print('Обучение пропущено: train_loader не инициализирован')
    elif len(train_loader.dataset) == 0:
        print('Обучение пропущено: пустая обучающая выборка')
    else:
        # Вычисление по возможности на графическом ускорителе
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        model.to(device)

        start_epoch = int(resume_epoch) if isinstance(resume_epoch, int) else 0
        if start_epoch >= num_epochs:
            start_epoch = 0
        best_val_loss = best_val_loss_resume if best_val_loss_resume is not None else float('inf')
        epochs_without_improvement = 0
        train_losses_history = []
        val_losses_history = []
        epoch_index_history = []

        for epoch in range(start_epoch, num_epochs):
            model.train()
            train_loss = 0.0
            for batch_X, batch_y in train_loader:
                batch_X, batch_y = batch_X.to(device), batch_y.to(device)
                optimizer.zero_grad()
                outputs = model(batch_X)
                loss = criterion(outputs, batch_y)
                loss.backward()
                optimizer.step()
                train_loss += loss.item() * batch_X.size(0)

            train_loss /= len(train_loader.dataset)

            # Валидация
            model.eval()
            val_loss = None
            val_size = len(val_loader.dataset) if val_loader is not None else 0
            if val_loader is not None and val_size > 0:
                val_loss_accum = 0.0
                with torch.no_grad():
                    for batch_X, batch_y in val_loader:
                        batch_X, batch_y = batch_X.to(device), batch_y.to(device)
                        outputs = model(batch_X)
                        loss = criterion(outputs, batch_y)
                        val_loss_accum += loss.item() * batch_X.size(0)
                val_loss = val_loss_accum / val_size
                print(f'Epoch {epoch+1}/{num_epochs}, Train Loss: {train_loss:.4f}, Val Loss: {val_loss:.4f}')
            else:
                print(f'Epoch {epoch+1}/{num_epochs}, Train Loss: {train_loss:.4f}, Val Loss: N/A (нет валидационных данных)')

            epoch_index_history.append(epoch + 1)
            train_losses_history.append(train_loss)
            val_losses_history.append(val_loss)

            # Live-визуализация процесса обучения по эпохам
            clear_output(wait=True)
            plt.figure(figsize=(10, 5))
            plt.plot(epoch_index_history, train_losses_history, label='Train Loss', linewidth=2)
            val_pairs_live = [(e, v) for e, v in zip(epoch_index_history, val_losses_history) if v is not None]
            if val_pairs_live:
                val_epochs_live = [p[0] for p in val_pairs_live]
                val_vals_live = [p[1] for p in val_pairs_live]
                plt.plot(val_epochs_live, val_vals_live, label='Val Loss', linewidth=2)
            plt.title('Обучение модели: динамика функции потерь (live)')
            plt.xlabel('Эпоха')
            plt.ylabel('Loss')
            plt.legend()
            plt.grid(True, alpha=0.3)
            plt.show()

            metric_for_selection = val_loss if val_loss is not None else train_loss
            if metric_for_selection + early_stopping_min_delta < best_val_loss:
                best_val_loss = metric_for_selection
                epochs_without_improvement = 0
                if checkpoint_path is not None:
                    torch.save(
                        {
                            'epoch': epoch + 1,
                            'model_state_dict': model.state_dict(),
                            'optimizer_state_dict': optimizer.state_dict(),
                            'best_val_loss': best_val_loss,
                            'hidden_dims': selected_hidden_dims
                        },
                        checkpoint_path
                    )
            else:
                epochs_without_improvement += 1

            if use_early_stopping and epochs_without_improvement >= early_stopping_patience:
                print(f'Ранняя остановка: нет улучшения {early_stopping_patience} эпох подряд')
                break

        if epoch_index_history:
            plt.figure(figsize=(10, 5))
            plt.plot(epoch_index_history, train_losses_history, label='Train Loss', linewidth=2)

            val_pairs = [(e, v) for e, v in zip(epoch_index_history, val_losses_history) if v is not None]
            if val_pairs:
                val_epochs = [p[0] for p in val_pairs]
                val_vals = [p[1] for p in val_pairs]
                plt.plot(val_epochs, val_vals, label='Val Loss', linewidth=2)

            plt.title('Обучение модели: динамика функции потерь')
            plt.xlabel('Эпоха')
            plt.ylabel('Loss')
            plt.legend()
            plt.grid(True, alpha=0.3)
            plt.show()

            # Резюме обучения и рекомендации
            last_epoch = epoch_index_history[-1]
            first_train = train_losses_history[0]
            last_train = train_losses_history[-1]
            best_train = min(train_losses_history)
            best_train_epoch = epoch_index_history[train_losses_history.index(best_train)]

            has_val = any(v is not None for v in val_losses_history)
            if has_val:
                val_only = [v for v in val_losses_history if v is not None]
                val_only_epochs = [e for e, v in zip(epoch_index_history, val_losses_history) if v is not None]
                first_val = val_only[0]
                last_val = val_only[-1]
                best_val = min(val_only)
                best_val_epoch = val_only_epochs[val_only.index(best_val)]
                generalization_gap = last_val - last_train

                print('\n=== РЕЗЮМЕ ОБУЧЕНИЯ ===')
                print(f'Эпох выполнено: {last_epoch}')
                print(f'Train loss: старт={first_train:.4f}, лучший={best_train:.4f} (эпоха {best_train_epoch}), финальный={last_train:.4f}')
                print(f'Val loss:   старт={first_val:.4f}, лучший={best_val:.4f} (эпоха {best_val_epoch}), финальный={last_val:.4f}')
                print(f'Generalization gap (val-train, финал): {generalization_gap:.4f}')

                print('\n=== РЕКОМЕНДАЦИИ ===')
                if generalization_gap > max(50.0, 0.2 * abs(last_val)):
                    print('- Признак переобучения: большой разрыв train/val.')
                    print('- Рекомендуется усилить регуляризацию (dropout/weight_decay) и упростить топологию.')
                    print('- Проверьте качество split (временной/стратифицированный) и достаточность валидации.')
                elif last_val > first_val * 0.99:
                    print('- Валидация почти не улучшается.')
                    print('- Рекомендуется пересмотреть признаки, learning_rate и диапазон топологий в GA.')
                else:
                    print('- Есть улучшение на валидации, конфигурация выглядит рабочей.')
                    print('- Рекомендуется запустить финальное дообучение и сохранить лучший checkpoint.')
            else:
                print('\n=== РЕЗЮМЕ ОБУЧЕНИЯ ===')
                print(f'Эпох выполнено: {last_epoch}')
                print(f'Train loss: старт={first_train:.4f}, лучший={best_train:.4f} (эпоха {best_train_epoch}), финальный={last_train:.4f}')
                print('Val loss: отсутствует (нет валидационной выборки).')

                print('\n=== РЕКОМЕНДАЦИИ ===')
                print('- Добавьте валидационный набор для контроля обобщающей способности.')
                print('- Без val метрики сложно корректно настраивать раннюю остановку и GA-поиск.')
except Exception as e:
    print(f'Ошибка в процессе обучения: {e}')

# %%

# Безопасное закрытие соединения с БД
try:
    if tp_cur is not None:
        tp_cur.close()
    if tp_con is not None:
        tp_con.close()
    print('Соединение с БД закрыто')
except Exception as e:
    print(f'Ошибка при закрытии соединения с БД: {e}')
