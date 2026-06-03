from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.ticker import FuncFormatter

from src.analysis import (
    fetch_course_revenue,
    fetch_error_area_counts,
    fetch_preview_watch_conversion,
    fetch_session_funnel,
)


CHART_DIR = Path(__file__).resolve().parent.parent / "charts"
FONT_DIR = Path(__file__).resolve().parent.parent / "assets" / "fonts"
FONT_REGULAR_PATH = FONT_DIR / "Pretendard-Regular.otf"
FONT_SEMIBOLD_PATH = FONT_DIR / "Pretendard-SemiBold.otf"
GRID_COLOR = "#e5e7eb"
TEXT_COLOR = "#111827"
MUTED_TEXT_COLOR = "#475569"
ACCENT_COLOR = "#f97316"
FUNNEL_COLORS = ["#93c5fd", "#60a5fa", "#2563eb", ACCENT_COLOR]
WATCH_COLORS = ["#dbeafe", "#bfdbfe", "#93c5fd", "#60a5fa"]
REVENUE_COLORS = [ACCENT_COLOR, "#2563eb", "#3b82f6", "#60a5fa", "#93c5fd"]
ERROR_COLORS = {
    "payment": "#ef4444",
    "live_class": ACCENT_COLOR,
    "lesson": "#64748b",
    "video": "#94a3b8",
}
DEFAULT_FOOTNOTE = "Synthetic event data · session 기준 집계 · 과제 검증용 데이터"

COURSE_SHORT_LABELS = {
    "course_class_setup": "클래스 세팅",
    "course_zoom_basic": "Zoom 기초",
    "course_liveklass_atoz": "Liveklass A-Z",
    "course_content_monetization": "콘텐츠 수익화",
    "course_content_planning": "콘텐츠 기획",
}

FUNNEL_LABELS = {
    "course_view": "강의 상세 조회",
    "lesson_started": "무료 체험 시청",
    "checkout_started": "결제 시작",
    "purchase_completed": "결제 완료",
}

ERROR_LABELS = {
    "payment": "결제",
    "live_class": "라이브 수업",
    "lesson": "강의 로딩",
    "video": "영상",
}

WATCH_BUCKET_LABELS = {
    "0-60s": "0-60초",
    "60-180s": "60-180초",
    "180-300s": "180-300초",
    "300s+": "300초 이상",
}


def main() -> None:
    _configure_font()
    CHART_DIR.mkdir(parents=True, exist_ok=True)

    draw_session_funnel()
    draw_preview_watch_conversion()
    draw_course_revenue()
    draw_error_area_counts()

    print(f"차트 PNG 생성 완료: {CHART_DIR}")


def draw_session_funnel() -> None:
    rows = fetch_session_funnel()
    labels = [FUNNEL_LABELS.get(step, step) for step, _, _, _ in rows]
    values = [session_count for _, session_count, _, _ in rows]
    from_start_rates = [from_start for _, _, from_start, _ in rows]
    from_previous_rates = [from_previous for _, _, _, from_previous in rows]
    start_count = values[0] if values else 0
    purchase_count = values[-1] if values else 0
    purchase_rate = from_start_rates[-1] if from_start_rates else 0

    fig, ax = _create_chart_figure()
    colors = FUNNEL_COLORS[: len(labels)]
    bars = ax.bar(labels, values, color=colors, width=0.62)
    _add_chart_context(
        fig,
        title="세션 퍼널 전환율",
        subtitle=(
            f"{start_count:,}개 세션 중 {purchase_count:,}개가 "
            f"구매 완료까지 도달했습니다 ({purchase_rate}%)."
        ),
    )
    _style_axes(ax, y_grid=True)
    ax.set_ylabel("세션 수")
    ax.set_ylim(0, max(values) * 1.42 if values else 1)
    ax.tick_params(axis="x", rotation=18)

    for index, (bar, value) in enumerate(zip(bars, values)):
        label = f"{value:,}\n시작 대비 {from_start_rates[index]}%"
        _label_vertical_bar(ax, bar, label, fontweight="semibold")

    if values:
        arrow_y = max(values) * 1.24
        for index, rate in enumerate(from_previous_rates[1:], start=1):
            ax.annotate(
                "",
                xy=(index - 0.18, arrow_y),
                xytext=(index - 0.82, arrow_y),
                arrowprops={
                    "arrowstyle": "->",
                    "color": MUTED_TEXT_COLOR,
                    "lw": 1.3,
                },
            )
            ax.text(
                index - 0.5,
                arrow_y + max(values) * 0.035,
                f"이전 대비 {rate}%",
                ha="center",
                va="bottom",
                fontsize=9,
                color=MUTED_TEXT_COLOR,
            )

    _finish_chart(fig, CHART_DIR / "session_funnel.png")


def draw_preview_watch_conversion() -> None:
    rows = fetch_preview_watch_conversion()
    labels = [WATCH_BUCKET_LABELS.get(bucket, bucket) for bucket, _, _, _ in rows]
    conversion_rates = [float(conversion_rate) for _, _, _, conversion_rate in rows]
    preview_counts = [preview_count for _, preview_count, _, _ in rows]
    purchase_counts = [purchase_count for _, _, purchase_count, _ in rows]
    max_index = (
        max(range(len(conversion_rates)), key=conversion_rates.__getitem__)
        if conversion_rates
        else 0
    )
    max_label = labels[max_index] if labels else "N/A"
    max_rate = conversion_rates[max_index] if conversion_rates else 0

    fig, ax = _create_chart_figure()
    colors = [
        ACCENT_COLOR if index == max_index else WATCH_COLORS[index]
        for index in range(len(labels))
    ]
    bars = ax.bar(labels, conversion_rates, color=colors, width=0.62)
    _add_chart_context(
        fig,
        title="무료 체험 시청 시간별 구매 전환율",
        subtitle=(
            f"{max_label} 시청 세션의 구매 전환율이 가장 높습니다 "
            f"({max_rate:.2f}%)."
        ),
    )
    _style_axes(ax, y_grid=True)
    ax.set_xlabel("시청 시간 구간")
    ax.set_ylabel("구매 전환율 (%)")
    ax.set_ylim(0, max(conversion_rates) * 1.34 if conversion_rates else 1)

    for index, (bar, rate, preview_count, purchase_count) in enumerate(zip(
        bars,
        conversion_rates,
        preview_counts,
        purchase_counts,
    )):
        label_y = max(rate, ax.get_ylim()[1] * 0.045)
        _label_vertical_bar(
            ax,
            bar,
            f"{rate:.2f}%\n구매 {purchase_count:,} / 시청 {preview_count:,}",
            y=label_y,
            fontweight="semibold" if index == max_index else "normal",
        )

    _finish_chart(fig, CHART_DIR / "preview_watch_conversion.png")


def draw_course_revenue() -> None:
    rows = fetch_course_revenue()
    labels = [COURSE_SHORT_LABELS.get(course_id, course_id) for course_id, _, _ in rows]
    revenues = [revenue for _, _, revenue in rows]
    purchase_counts = [purchase_count for _, purchase_count, _ in rows]
    top_purchase_index = (
        max(range(len(purchase_counts)), key=purchase_counts.__getitem__)
        if purchase_counts
        else 0
    )

    _draw_horizontal_bar(
        labels=labels,
        values=revenues,
        title="강의별 매출",
        subtitle=(
            f"매출 1위는 {labels[0]}, 구매 수 1위는 "
            f"{labels[top_purchase_index]}입니다."
            if labels
            else "강의별 매출과 구매 수를 함께 비교합니다."
        ),
        xlabel="매출 (만원)",
        output_path=CHART_DIR / "course_revenue.png",
        colors=REVENUE_COLORS[: len(labels)],
        value_formatter=lambda index, value: (
            f"{value / 10_000:,.0f}만 원 / 구매 {purchase_counts[index]:,}건"
        ),
        xaxis_formatter=lambda value: f"{value / 10_000:.0f}만",
    )


def draw_error_area_counts() -> None:
    rows = fetch_error_area_counts()
    labels = [ERROR_LABELS.get(error_area, error_area) for error_area, _ in rows]
    values = [count for _, count in rows]
    total_errors = sum(values)
    percentages = [
        value / total_errors * 100
        if total_errors
        else 0
        for value in values
    ]
    top_label = labels[0] if labels else "N/A"
    top_share = percentages[0] if percentages else 0
    colors = [
        ERROR_COLORS.get(error_area, "#94a3b8")
        if error_area == "payment"
        else "#94a3b8"
        for error_area, _ in rows
    ]

    _draw_horizontal_bar(
        labels=labels,
        values=values,
        title="오류 영역별 발생 수",
        subtitle=(
            f"{top_label} 오류가 전체 오류 중 가장 큰 비중을 차지합니다 "
            f"({top_share:.1f}%)."
        ),
        xlabel="오류 수",
        output_path=CHART_DIR / "error_area_counts.png",
        colors=colors,
        value_formatter=lambda index, value: (
            f"{value:,}건 ({percentages[index]:.1f}%)"
        ),
    )


def _draw_horizontal_bar(
    *,
    labels: list[str],
    values: list[int],
    title: str,
    subtitle: str,
    xlabel: str,
    output_path: Path,
    colors: list[str],
    value_formatter: Callable[[int, int], str] | None = None,
    xaxis_formatter: Callable[[float], str] | None = None,
) -> None:
    fig, ax = _create_chart_figure()
    bars = ax.barh(labels, values, color=colors)
    ax.invert_yaxis()
    _add_chart_context(fig, title=title, subtitle=subtitle)
    _style_axes(ax, x_grid=True)
    ax.set_xlabel(xlabel)
    ax.set_xlim(0, max(values) * 1.38 if values else 1)
    if xaxis_formatter is not None:
        ax.xaxis.set_major_formatter(
            FuncFormatter(lambda value, _: xaxis_formatter(value))
        )

    formatter = value_formatter or (lambda _, value: f"{value:,}")
    max_value = max(values) if values else 0
    offset = max_value * 0.01 if max_value else 1

    for index, (bar, value) in enumerate(zip(bars, values)):
        ax.text(
            value + offset,
            bar.get_y() + bar.get_height() / 2,
            formatter(index, value),
            va="center",
            fontsize=10,
            color=TEXT_COLOR,
        )

    _finish_chart(fig, output_path)


def _style_axes(
    ax: plt.Axes,
    *,
    x_grid: bool = False,
    y_grid: bool = False,
) -> None:
    ax.set_facecolor("white")
    ax.figure.set_facecolor("white")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#cbd5e1")
    ax.spines["bottom"].set_color("#cbd5e1")
    ax.tick_params(axis="both", colors=TEXT_COLOR, labelsize=10)
    ax.xaxis.label.set_color(MUTED_TEXT_COLOR)
    ax.yaxis.label.set_color(MUTED_TEXT_COLOR)
    ax.set_axisbelow(True)
    if x_grid:
        ax.grid(axis="x", color=GRID_COLOR, linewidth=0.8)
    if y_grid:
        ax.grid(axis="y", color=GRID_COLOR, linewidth=0.8)


def _create_chart_figure() -> tuple[plt.Figure, plt.Axes]:
    return plt.subplots(figsize=(9, 5.6))


def _add_chart_context(
    fig: plt.Figure,
    *,
    title: str,
    subtitle: str,
    footnote: str = DEFAULT_FOOTNOTE,
) -> None:
    fig.text(
        0.075,
        0.955,
        title,
        ha="left",
        va="top",
        fontsize=17,
        fontweight="bold",
        color=TEXT_COLOR,
    )
    fig.text(
        0.075,
        0.905,
        subtitle,
        ha="left",
        va="top",
        fontsize=10.5,
        color=MUTED_TEXT_COLOR,
    )
    fig.text(
        0.075,
        0.03,
        footnote,
        ha="left",
        va="bottom",
        fontsize=8.5,
        color=MUTED_TEXT_COLOR,
    )


def _configure_font() -> None:
    for font_path in (FONT_REGULAR_PATH, FONT_SEMIBOLD_PATH):
        font_manager.fontManager.addfont(font_path)

    font_name = font_manager.FontProperties(fname=FONT_REGULAR_PATH).get_name()
    plt.rcParams["font.family"] = font_name
    plt.rcParams["axes.unicode_minus"] = False


def _label_vertical_bar(
    ax: plt.Axes,
    bar: plt.Rectangle,
    label: str,
    *,
    y: float | None = None,
    fontweight: str = "normal",
) -> None:
    label_y = bar.get_height() if y is None else y
    ax.text(
        bar.get_x() + bar.get_width() / 2,
        label_y,
        label,
        ha="center",
        va="bottom",
        fontsize=9,
        fontweight=fontweight,
        color=TEXT_COLOR,
    )


def _finish_chart(fig: plt.Figure, output_path: Path) -> None:
    fig.tight_layout(rect=(0.045, 0.075, 0.985, 0.86))
    fig.savefig(output_path, dpi=160, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    main()
