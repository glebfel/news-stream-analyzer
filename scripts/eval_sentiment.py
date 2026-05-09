import argparse
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "libs" / "common" / "src"))
sys.path.insert(0, str(ROOT / "services" / "nlp_worker" / "src"))

from news_common.models import SentimentLabel  # noqa: E402
from nlp_worker.services.sentiment import build_sentiment_service  # noqa: E402

METRICS_DIR = ROOT / "docs" / "metrics"

# Hand-labelled held-out set, balanced across positive / negative / neutral.
BUILTIN_SET: list[tuple[str, SentimentLabel]] = [
    # positive
    ("Сборная России выиграла чемпионат мира по хоккею", SentimentLabel.POSITIVE),
    ("Курс рубля заметно укрепился после новостей о соглашении", SentimentLabel.POSITIVE),
    ("Учёные сделали важное открытие в области медицины", SentimentLabel.POSITIVE),
    ("Компания показала рекордный рост прибыли в третьем квартале", SentimentLabel.POSITIVE),
    ("Открытие нового технопарка прошло успешно", SentimentLabel.POSITIVE),
    ("Президент наградил выдающихся учёных за вклад в науку", SentimentLabel.POSITIVE),
    (
        "Студенты ВШЭ победили в международной олимпиаде по программированию",
        SentimentLabel.POSITIVE,
    ),
    ("Запуск нового спутника завершился полным успехом", SentimentLabel.POSITIVE),
    ("В стране зафиксирован рекордный урожай зерновых", SentimentLabel.POSITIVE),
    ("Уровень безработицы снизился до исторического минимума", SentimentLabel.POSITIVE),
    ("Подписано важное соглашение о сотрудничестве", SentimentLabel.POSITIVE),
    ("Спортсмен установил новый мировой рекорд", SentimentLabel.POSITIVE),
    ("Прорыв в исследовании раковых заболеваний", SentimentLabel.POSITIVE),
    ("Городские власти объявили о запуске нового парка", SentimentLabel.POSITIVE),
    ("Завод показал лучший за десять лет результат", SentimentLabel.POSITIVE),
    ("Российская команда заняла первое место на международном конкурсе", SentimentLabel.POSITIVE),
    ("Получено одобрение нового препарата против вирусных инфекций", SentimentLabel.POSITIVE),
    ("Турпоток в регионе увеличился вдвое", SentimentLabel.POSITIVE),
    ("Состоялась успешная стыковка корабля с орбитальной станцией", SentimentLabel.POSITIVE),
    ("Открыт новый роддом, оснащённый по последнему слову техники", SentimentLabel.POSITIVE),
    # negative
    ("Курс рубля резко упал после введения новых санкций", SentimentLabel.NEGATIVE),
    ("В результате ДТП на трассе погибли пять человек", SentimentLabel.NEGATIVE),
    ("Хакерская атака парализовала работу крупнейшего банка", SentimentLabel.NEGATIVE),
    ("Министр финансов подал в отставку на фоне кризиса", SentimentLabel.NEGATIVE),
    ("Компания объявила о массовых увольнениях сотрудников", SentimentLabel.NEGATIVE),
    ("Экономический кризис продолжает углубляться", SentimentLabel.NEGATIVE),
    ("Крупный пожар уничтожил несколько домов в посёлке", SentimentLabel.NEGATIVE),
    ("Санкции введены против ряда российских компаний", SentimentLabel.NEGATIVE),
    ("Утечка персональных данных миллионов клиентов", SentimentLabel.NEGATIVE),
    ("В стране объявлен дефолт по внешним обязательствам", SentimentLabel.NEGATIVE),
    ("Завод прекратил работу из-за нехватки сырья", SentimentLabel.NEGATIVE),
    ("Уголовное дело возбуждено против бывшего министра", SentimentLabel.NEGATIVE),
    ("В ДТП погиб известный спортсмен", SentimentLabel.NEGATIVE),
    ("Падение акций компании составило 20% за день", SentimentLabel.NEGATIVE),
    ("Произошла серьёзная авария на нефтеперерабатывающем заводе", SentimentLabel.NEGATIVE),
    ("Разразился громкий коррупционный скандал", SentimentLabel.NEGATIVE),
    ("Серьёзное ограничение работы транспорта из-за непогоды", SentimentLabel.NEGATIVE),
    ("Введён режим чрезвычайной ситуации в нескольких регионах", SentimentLabel.NEGATIVE),
    ("Атака беспилотников нанесла серьёзный ущерб инфраструктуре", SentimentLabel.NEGATIVE),
    ("Зафиксирован рост числа случаев тяжёлых заболеваний", SentimentLabel.NEGATIVE),
    # neutral
    ("Совещание правительства состоялось сегодня в Кремле", SentimentLabel.NEUTRAL),
    ("Министр посетил завод и осмотрел производственные линии", SentimentLabel.NEUTRAL),
    ("Международная конференция начнётся в среду в десять утра", SentimentLabel.NEUTRAL),
    ("Опубликованы новые данные о численности населения региона", SentimentLabel.NEUTRAL),
    ("Состоялось плановое заседание профильного комитета", SentimentLabel.NEUTRAL),
    ("Президент принял посла иностранного государства", SentimentLabel.NEUTRAL),
    ("Отчёт будет представлен в следующем месяце на сессии", SentimentLabel.NEUTRAL),
    ("Прошла встреча с участием отраслевых экспертов", SentimentLabel.NEUTRAL),
    ("Документ был передан в министерство для рассмотрения", SentimentLabel.NEUTRAL),
    ("Цены на нефть остались на прежнем уровне", SentimentLabel.NEUTRAL),
    ("В Москве объявлено о начале строительства новой школы", SentimentLabel.NEUTRAL),
    ("Эксперты обсудили перспективы рынка на форуме", SentimentLabel.NEUTRAL),
    ("Поезд прибыл на конечную станцию по расписанию", SentimentLabel.NEUTRAL),
    ("Глава региона провёл рабочую поездку по предприятиям", SentimentLabel.NEUTRAL),
    ("Был представлен новый план развития транспорта", SentimentLabel.NEUTRAL),
    ("Проведено заседание попечительского совета университета", SentimentLabel.NEUTRAL),
    ("Министерство опубликовало проект изменений в законодательстве", SentimentLabel.NEUTRAL),
    ("Делегация прибыла с официальным визитом", SentimentLabel.NEUTRAL),
    ("Состоялся ежегодный отчёт перед советом директоров", SentimentLabel.NEUTRAL),
    ("На заседании рассмотрены поправки к бюджету", SentimentLabel.NEUTRAL),
]


def load_huggingface(name: str, limit: int | None) -> list[tuple[str, SentimentLabel]]:
    try:
        from datasets import load_dataset
    except Exception as exc:
        print(f"datasets library not available: {exc}", file=sys.stderr)
        return []

    try:
        ds = load_dataset(name, split="test")
    except Exception:
        try:
            ds = load_dataset(name, split="train")
        except Exception as exc:
            print(f"failed to load HF dataset {name}: {exc}", file=sys.stderr)
            return []

    out: list[tuple[str, SentimentLabel]] = []
    for row in ds:
        text = row.get("text") or row.get("review") or row.get("sentence") or ""
        raw_label = row.get("label", row.get("sentiment", -1))
        if isinstance(raw_label, int):
            # MonoHime label codes: 0=neutral, 1=positive, 2=negative.
            mapping = {
                0: SentimentLabel.NEUTRAL,
                1: SentimentLabel.POSITIVE,
                2: SentimentLabel.NEGATIVE,
            }
            label = mapping.get(raw_label)
        elif isinstance(raw_label, str):
            label = (
                SentimentLabel(raw_label)
                if raw_label in {"positive", "negative", "neutral"}
                else None
            )
        else:
            label = None
        if text and label is not None:
            out.append((text, label))
        if limit and len(out) >= limit:
            break
    return out


def evaluate(samples, service) -> tuple[float, dict]:
    per_class = defaultdict(lambda: {"tp": 0, "fp": 0, "fn": 0, "support": 0})
    correct = 0
    confusion: dict[tuple[str, str], int] = defaultdict(int)
    for text, gold in samples:
        pred, _ = service.predict(text)
        per_class[gold]["support"] += 1
        confusion[(gold.value, pred.value)] += 1
        if pred == gold:
            correct += 1
            per_class[gold]["tp"] += 1
        else:
            per_class[gold]["fn"] += 1
            per_class[pred]["fp"] += 1
    accuracy = correct / len(samples) if samples else 0.0
    return accuracy, {"per_class": dict(per_class), "confusion": dict(confusion)}


def render_markdown(
    accuracy: float,
    metrics: dict,
    n: int,
    source: str,
    mode: str,
) -> str:
    today = datetime.utcnow().strftime("%Y-%m-%d")
    lines = [
        "# Sentiment evaluation",
        "",
        f"Date: {today}  ",
        f"Examples evaluated: {n}  ",
        f"Source: {source}  ",
        f"Backend: SentimentService (mode={mode})",
        "",
        f"## Overall accuracy: **{accuracy:.3f}**",
        "",
        "| Class | Precision | Recall | F1 | Support |",
        "|-------|-----------|--------|-----|---------|",
    ]
    per = metrics["per_class"]
    classes = [SentimentLabel.POSITIVE, SentimentLabel.NEGATIVE, SentimentLabel.NEUTRAL]
    macro_p = macro_r = macro_f = 0.0
    for cls in classes:
        m = per.get(cls, {"tp": 0, "fp": 0, "fn": 0, "support": 0})
        p = m["tp"] / (m["tp"] + m["fp"]) if (m["tp"] + m["fp"]) else 0.0
        r = m["tp"] / (m["tp"] + m["fn"]) if (m["tp"] + m["fn"]) else 0.0
        f = 2 * p * r / (p + r) if (p + r) else 0.0
        lines.append(f"| {cls.value} | {p:.3f} | {r:.3f} | {f:.3f} | {m['support']} |")
        macro_p += p
        macro_r += r
        macro_f += f
    n_classes = len(classes)
    lines += [
        "",
        f"**Macro-averaged:** precision={macro_p / n_classes:.3f} "
        f"recall={macro_r / n_classes:.3f} F1={macro_f / n_classes:.3f}",
        "",
        "## Confusion matrix",
        "",
        "| gold \\ pred | positive | negative | neutral |",
        "|-------------|----------|----------|---------|",
    ]
    for gold in classes:
        row = [f"| **{gold.value}** "]
        for pred in classes:
            row.append(f"| {metrics['confusion'].get((gold.value, pred.value), 0)} ")
        row.append("|")
        lines.append("".join(row))
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["lite", "full"], default="lite")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument(
        "--builtin", action="store_true", help="Skip HF, use built-in test set only"
    )
    parser.add_argument(
        "--hf-dataset", default="MonoHime/ru_sentiment_dataset", help="HF dataset id"
    )
    args = parser.parse_args()

    METRICS_DIR.mkdir(parents=True, exist_ok=True)
    service = build_sentiment_service(args.mode)
    print(f"Sentiment service ready (mode={args.mode})", flush=True)

    if args.builtin:
        samples = list(BUILTIN_SET)
        source = "built-in held-out set (60 hand-labelled news examples)"
    else:
        samples = load_huggingface(args.hf_dataset, args.limit)
        if samples:
            source = f"HuggingFace dataset {args.hf_dataset}"
        else:
            samples = list(BUILTIN_SET)
            source = "built-in held-out set (HF dataset unavailable, fell back)"

    if args.limit:
        samples = samples[: args.limit]

    accuracy, metrics = evaluate(samples, service)
    md = render_markdown(accuracy, metrics, len(samples), source, args.mode)
    out_path = METRICS_DIR / f"sentiment_{args.mode}_{datetime.utcnow().strftime('%Y-%m-%d')}.md"
    out_path.write_text(md, encoding="utf-8")
    print(f"\nwritten to {out_path}\n")
    print(md)


if __name__ == "__main__":
    main()
