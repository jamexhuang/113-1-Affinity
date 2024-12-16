# ============================================
# AFFINITY的財務狀況模擬 (凸性指數型下降從第3個月開始)
# ============================================

import matplotlib.pyplot as plt
import os

# ============================================
# 各項假設因子
# ============================================

# 總模擬月份
MONTHS_TOTAL = 36

# 樂觀(Baseline)假設因子
BASELINE_INITIAL_GROWTH_RATE = 0.34       # 初期成長率（高）
BASELINE_FINAL_GROWTH_RATE = 0.03         # 終期成長率（低）
BASELINE_MONTHLY_SUB_PRICE = 320          # 月訂閱費
BASELINE_ANNUAL_SUB_PRICE = 3200          # 年訂閱費
BASELINE_SUBSCRIPTION_RATE = 0.02         # 訂閱率（MAU中有多少比例付費訂閱）
BASELINE_RPM = 65                        # 每千非訂閱用戶的廣告收入 (約2 USD)
BASELINE_PERSONNEL_COST_LOW = 140000      # 前兩個月的人事成本（低月）
BASELINE_PERSONNEL_COST_HIGH = 280000     # 後續月份的人事成本（高月）
BASELINE_OPERATIONAL_COST = 53968         # 固定管銷費用（例如伺服器、店租等）

# 悲觀(Conservative)假設因子 (在樂觀基礎上降低)
CONSERVATIVE_INITIAL_GROWTH_RATE = BASELINE_INITIAL_GROWTH_RATE * 0.8
CONSERVATIVE_FINAL_GROWTH_RATE = BASELINE_FINAL_GROWTH_RATE * 0.8
CONSERVATIVE_MONTHLY_SUB_PRICE = BASELINE_MONTHLY_SUB_PRICE * 1
CONSERVATIVE_ANNUAL_SUB_PRICE = BASELINE_ANNUAL_SUB_PRICE * 1
CONSERVATIVE_SUBSCRIPTION_RATE = BASELINE_SUBSCRIPTION_RATE * 0.8
CONSERVATIVE_RPM = BASELINE_RPM * 0.8
# 人事成本與管銷費用在悲觀情境下不變
CONSERVATIVE_PERSONNEL_COST_LOW = BASELINE_PERSONNEL_COST_LOW
CONSERVATIVE_PERSONNEL_COST_HIGH = BASELINE_PERSONNEL_COST_HIGH
CONSERVATIVE_OPERATIONAL_COST = BASELINE_OPERATIONAL_COST

# 初始資金
INITIAL_CAPITAL = 6200000

# 高亮月份
HIGHLIGHT_MONTHS = [1, 6, 12, 18, 24, 30, 36]

# ============================================
# 以下為程式主體與繪圖函式
# ============================================

def save_individual_fig(fig, filename):
    output_dir = os.path.expanduser("~/Downloads/tmp")
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, filename)
    fig.savefig(filepath, dpi=300, bbox_inches='tight')
    print(f"圖表已儲存至: {filepath}")
    plt.close(fig)  # 關閉圖表以節省記憶體

def calculate_mau(months_total, initial_growth_rate, final_growth_rate):
    mau_data = [0, 0]  # 前兩個月 MAU 為 0，第三個月(程式的month=2)開始有成長
    for month in range(2, months_total):
        # month=2 (第三個月) 時 ratio=0，growth_rate=initial_growth_rate
        # month=months_total-1 時 ratio=1，growth_rate=final_growth_rate
        ratio = (month - 2) / (months_total - 3)
        growth_rate = initial_growth_rate * ((final_growth_rate / initial_growth_rate) ** (ratio**2))
        new_mau = (mau_data[-1] if month > 2 else 1000) * (1 + growth_rate)
        mau_data.append(new_mau)
    return mau_data

def calculate_revenues(mau_data, months_total, subscription_rate, monthly_subscription_price, annual_subscription_price, rpm):
    subscription_revenue, ad_revenue, monthly_revenue = [], [], []
    for month in range(months_total):
        if month < 2:
            subscription_revenue.append(0)
            ad_revenue.append(0)
            monthly_revenue.append(0)
        else:
            mau = mau_data[month]
            sub_revenue = mau * subscription_rate * (monthly_subscription_price + (annual_subscription_price / 12))
            ads_revenue = mau * (1 - subscription_rate) * rpm / 1000
            total_revenue = sub_revenue + ads_revenue
            subscription_revenue.append(sub_revenue)
            ad_revenue.append(ads_revenue)
            monthly_revenue.append(total_revenue)
    return subscription_revenue, ad_revenue, monthly_revenue

def calculate_cash_flow(monthly_revenue, months_total, personnel_cost_low, personnel_cost_high, operational_cost):
    personnel_costs = [personnel_cost_low if month < 2 else personnel_cost_high for month in range(months_total)]
    cash_flow = [monthly_revenue[month] - personnel_costs[month] - operational_cost for month in range(months_total)]
    cumulative_surplus = [sum(cash_flow[:month + 1]) for month in range(months_total)]
    breakeven_month = next((month + 1 for month in range(months_total) if cumulative_surplus[month] >= 0), None)
    return cash_flow, cumulative_surplus, breakeven_month

def annotate_highlight_points(ax, x_data, y_data, highlight_months, color='red', bbox_props=None):
    y_min, y_max = min(y_data), max(y_data)
    offset = (y_max - y_min) * 0.05 if y_max != y_min else 10

    if bbox_props is None:
        bbox_props = dict(boxstyle="round,pad=0.3", edgecolor=color, facecolor="white")

    for month in highlight_months:
        value = y_data[month - 1]
        ax.scatter(month, value, color=color, edgecolor='black', zorder=10, s=100)
        ax.text(month, value + offset, f"{int(value):,}", ha='center', fontsize=9, color=color, bbox=bbox_props)

def annotate_breakeven(ax, breakeven_month, chart_type, breakeven_data):
    if breakeven_month and breakeven_data and 'value' in breakeven_data and 'label' in breakeven_data:
        month = breakeven_data['month']
        val = breakeven_data['value']
        label = breakeven_data['label']

        y_min, y_max = ax.get_ylim()
        offset = (y_max - y_min) * 0.1 if y_max != y_min else 10

        ax.axvline(month, color='green', linestyle='--', linewidth=1.5, label='Breakeven')

        info_text = f"Month: {month}\n{label}: {int(val):,}"

        ax.text(
            month, val + offset, info_text, color='green', fontsize=10, ha='center',
            bbox=dict(boxstyle="round,pad=0.3", edgecolor='blue', facecolor="white")
        )
    else:
        ax.text(
            0.95, 0.95, 'No Breakeven Point in this scenario',
            transform=ax.transAxes, fontsize=12, color='red', ha='right', va='top',
            bbox=dict(boxstyle="round,pad=0.3", edgecolor='red', facecolor="white")
        )

def plot_scenario(
    scenario_name,
    months_total,
    initial_growth_rate,
    final_growth_rate,
    monthly_subscription_price,
    annual_subscription_price,
    subscription_rate,
    rpm,
    personnel_cost_low,
    personnel_cost_high,
    operational_cost,
    initial_capital,
    highlight_months
):
    # 計算數據
    mau_data = calculate_mau(months_total, initial_growth_rate, final_growth_rate)
    subscription_revenue, ad_revenue, monthly_revenue = calculate_revenues(
        mau_data, months_total, subscription_rate, monthly_subscription_price, annual_subscription_price, rpm
    )
    cash_flow, cumulative_surplus, breakeven_month = calculate_cash_flow(
        monthly_revenue, months_total, personnel_cost_low, personnel_cost_high, operational_cost
    )

    # 計算成長率（同一公式）
    growth_rates = []
    for month in range(months_total):
        if month < 2:
            g = 0
        else:
            ratio = (month - 2) / (months_total - 3)
            g = initial_growth_rate * ((final_growth_rate / initial_growth_rate) ** (ratio**2))
        growth_rates.append(g)
    growth_rates_percent = [rate * 100 for rate in growth_rates]

    cash_balance = [initial_capital + cs for cs in cumulative_surplus]
    total_revenue = [sr + ar for sr, ar in zip(subscription_revenue, ad_revenue)]

    if breakeven_month:
        idx = breakeven_month - 1
    else:
        idx = None

    # 圖1：每月營收（區分訂閱與廣告）
    fig1, ax1 = plt.subplots(figsize=(10, 8))
    ax1.bar(range(1, months_total + 1), subscription_revenue, color='#4CAF50', label='Subscription Revenue', alpha=0.8)
    ax1.bar(range(1, months_total + 1), ad_revenue, bottom=subscription_revenue, color='#FF9800', label='Ad Revenue', alpha=0.8)
    annotate_highlight_points(ax1, range(1, months_total + 1), total_revenue, highlight_months)
    if breakeven_month:
        annotate_breakeven(ax1, breakeven_month, 'revenue_breakdown', {
            'month': breakeven_month,
            'value': total_revenue[idx],
            'label': 'Monthly Revenue'
        })
    ax1.set_title(f'{scenario_name}: Monthly Revenue Breakdown (Subscription vs Ad)', fontweight='bold')
    ax1.set_xlabel('Months')
    ax1.set_ylabel('Revenue (TWD)')
    ax1.legend(loc='upper left')
    ax1.grid(linestyle='--', alpha=0.7)
    save_individual_fig(fig1, f"{scenario_name.lower()}_monthly_revenue_breakdown.png")

    # 圖2：MAU 成長
    fig2, ax2 = plt.subplots(figsize=(10, 8))
    ax2.plot(range(1, months_total + 1), mau_data, marker='o', linewidth=2.5, color='#1E88E5', label='MAU Growth')
    annotate_highlight_points(ax2, range(1, months_total + 1), mau_data, highlight_months)
    if breakeven_month:
        annotate_breakeven(ax2, breakeven_month, 'mau', {
            'month': breakeven_month,
            'value': mau_data[idx],
            'label': 'MAU'
        })
    ax2.set_title(f'{scenario_name}: MAU Growth Over Time', fontweight='bold')
    ax2.set_xlabel('Months')
    ax2.set_ylabel('MAU')
    ax2.grid(linestyle='--', alpha=0.7)
    save_individual_fig(fig2, f"{scenario_name.lower()}_mau_growth.png")

    # 圖3：每月總收益
    fig3, ax3 = plt.subplots(figsize=(10, 8))
    ax3.plot(range(1, months_total + 1), monthly_revenue, marker='o', linewidth=2.5, color='#4CAF50')
    annotate_highlight_points(ax3, range(1, months_total + 1), monthly_revenue, highlight_months)
    if breakeven_month:
        annotate_breakeven(ax3, breakeven_month, 'revenue', {
            'month': breakeven_month,
            'value': monthly_revenue[idx],
            'label': 'Monthly Revenue'
        })
    ax3.set_title(f'{scenario_name}: Monthly Revenue Over Time', fontweight='bold')
    ax3.set_xlabel('Months')
    ax3.set_ylabel('Revenue (TWD)')
    ax3.grid(linestyle='--', alpha=0.7)
    save_individual_fig(fig3, f"{scenario_name.lower()}_monthly_revenue_over_time.png")

    # 圖4：每月現金流
    fig4, ax4 = plt.subplots(figsize=(10, 8))
    ax4.plot(range(1, months_total + 1), cash_flow, marker='o', linewidth=2.5, color='#673AB7', label='Monthly Cash Flow')
    annotate_highlight_points(ax4, range(1, months_total + 1), cash_flow, highlight_months)
    if breakeven_month:
        annotate_breakeven(ax4, breakeven_month, 'cash_flow', {
            'month': breakeven_month,
            'value': monthly_revenue[idx],
            'label': 'Monthly Revenue'
        })
    ax4.axhline(0, color='gray', linestyle='--', linewidth=1)
    ax4.set_title(f'{scenario_name}: Monthly Cash Flow Over Time', fontweight='bold')
    ax4.set_xlabel('Months')
    ax4.set_ylabel('Monthly Cash Flow (TWD)')
    ax4.grid(linestyle='--', alpha=0.7)
    ax4.legend()
    save_individual_fig(fig4, f"{scenario_name.lower()}_monthly_cash_flow.png")

    # 圖5：成長率遞減 (凸性指數型)
    fig5, ax5 = plt.subplots(figsize=(10, 8))
    ax5.plot(range(1, months_total + 1), growth_rates_percent, marker='o', linewidth=2.5, color='#FFA726')
    annotate_highlight_points(ax5, range(1, months_total + 1), growth_rates_percent, highlight_months)
    if breakeven_month:
        annotate_breakeven(ax5, breakeven_month, 'growth_rate', {
            'month': breakeven_month,
            'value': growth_rates_percent[idx],
            'label': 'Growth Rate (%)'
        })
    ax5.set_title(f'{scenario_name}: Growth Rate Decrease Over Time', fontweight='bold')
    ax5.set_xlabel('Months')
    ax5.set_ylabel('Growth Rate (%)')
    ax5.grid(linestyle='--', alpha=0.7)
    save_individual_fig(fig5, f"{scenario_name.lower()}_growth_rate_decrease.png")

    # 圖6：現金水位
    fig6, ax6 = plt.subplots(figsize=(10, 8))
    ax6.plot(range(1, months_total + 1), cash_balance, marker='o', linewidth=2.5, color='#009688', label='Cash Balance')
    annotate_highlight_points(ax6, range(1, months_total + 1), cash_balance, highlight_months)
    if breakeven_month:
        annotate_breakeven(ax6, breakeven_month, 'cash_balance', {
            'month': breakeven_month,
            'value': cash_balance[idx],
            'label': 'Cash Balance (TWD)'
        })
    ax6.axhline(initial_capital, color='gray', linestyle='--', linewidth=1, label='Initial Capital Level')
    ax6.set_title(f'{scenario_name}: Cash Balance Over Time', fontweight='bold')
    ax6.set_xlabel('Months')
    ax6.set_ylabel('Cash Balance (TWD)')
    ax6.grid(linestyle='--', alpha=0.7)
    ax6.legend()
    save_individual_fig(fig6, f"{scenario_name.lower()}_cash_balance.png")

    # 回傳資訊
    return {
        'initial_growth_rate': initial_growth_rate,
        'final_growth_rate': final_growth_rate,
        'monthly_subscription_price': monthly_subscription_price,
        'annual_subscription_price': annual_subscription_price,
        'subscription_rate': subscription_rate,
        'rpm': rpm,
        'breakeven_month': breakeven_month,
        'final_cumulative_surplus': cumulative_surplus[-1] if cumulative_surplus else 0
    }

def plot_and_save_individual_figs():
    # 樂觀（Baseline）情境參數
    baseline_params = {
        'months_total': MONTHS_TOTAL,
        'initial_growth_rate': BASELINE_INITIAL_GROWTH_RATE,
        'final_growth_rate': BASELINE_FINAL_GROWTH_RATE,
        'monthly_subscription_price': BASELINE_MONTHLY_SUB_PRICE,
        'annual_subscription_price': BASELINE_ANNUAL_SUB_PRICE,
        'subscription_rate': BASELINE_SUBSCRIPTION_RATE,
        'rpm': BASELINE_RPM,
        'personnel_cost_low': BASELINE_PERSONNEL_COST_LOW,
        'personnel_cost_high': BASELINE_PERSONNEL_COST_HIGH,
        'operational_cost': BASELINE_OPERATIONAL_COST,
        'initial_capital': INITIAL_CAPITAL,
        'highlight_months': HIGHLIGHT_MONTHS
    }

    # 悲觀（Conservative）情境參數
    conservative_params = {
        'months_total': MONTHS_TOTAL,
        'initial_growth_rate': CONSERVATIVE_INITIAL_GROWTH_RATE,
        'final_growth_rate': CONSERVATIVE_FINAL_GROWTH_RATE,
        'monthly_subscription_price': CONSERVATIVE_MONTHLY_SUB_PRICE,
        'annual_subscription_price': CONSERVATIVE_ANNUAL_SUB_PRICE,
        'subscription_rate': CONSERVATIVE_SUBSCRIPTION_RATE,
        'rpm': CONSERVATIVE_RPM,
        'personnel_cost_low': CONSERVATIVE_PERSONNEL_COST_LOW,
        'personnel_cost_high': CONSERVATIVE_PERSONNEL_COST_HIGH,
        'operational_cost': CONSERVATIVE_OPERATIONAL_COST,
        'initial_capital': INITIAL_CAPITAL,
        'highlight_months': HIGHLIGHT_MONTHS
    }

    # 繪製樂觀（Baseline）情境
    baseline_results = plot_scenario("Baseline", **baseline_params)

    # 繪製悲觀（Conservative）情境
    conservative_results = plot_scenario("Conservative", **conservative_params)

    # 新增比較圖表
    fig, ax = plt.subplots(figsize=(10, 8))
    factors = ['initial_growth_rate', 'final_growth_rate', 'monthly_subscription_price', 'annual_subscription_price', 'subscription_rate', 'rpm']
    baseline_values = [baseline_results[f] for f in factors]
    conservative_values = [conservative_results[f] for f in factors]

    x = range(len(factors))
    width = 0.4

    ax.bar([xi - width/2 for xi in x], baseline_values, width=width, label='Baseline', alpha=0.8)
    ax.bar([xi + width/2 for xi in x], conservative_values, width=width, label='Conservative', alpha=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels(factors, rotation=45, ha='right')
    ax.set_ylabel('Parameter Value')
    ax.set_title('Comparison of Key Assumptions: Baseline vs. Conservative', fontweight='bold')
    ax.legend()
    ax.grid(linestyle='--', alpha=0.7)

    explanation_text = (
        "This chart compares key assumptions between Baseline and Conservative scenarios.\n"
        "- Growth rates now start high in the 3rd month and exponentially decrease until the final month.\n"
        "In the Conservative scenario, growth rates and other factors are lower, reflecting a more pessimistic outlook."
    )

    fig.text(0.5, -0.2, explanation_text, ha='center', va='center', wrap=True, fontsize=10)
    save_individual_fig(fig, "assumption_comparison.png")

    # 在stdout輸出財務摘要
    print("\n==================== 財務摘要 ====================")
    print("Baseline Scenario:")
    if baseline_results['breakeven_month']:
        print(f"  有損益平衡點，於第 {baseline_results['breakeven_month']} 月達成。")
    else:
        print("  無法在預設期間內達到損益平衡。")
    print(f"  最終累積餘額: {int(baseline_results['final_cumulative_surplus']):,} TWD")

    print("\nConservative Scenario:")
    if conservative_results['breakeven_month']:
        print(f"  有損益平衡點，於第 {conservative_results['breakeven_month']} 月達成。")
    else:
        print("  無法在預設期間內達到損益平衡。")
    print(f"  最終累積餘額: {int(conservative_results['final_cumulative_surplus']):,} TWD")
    print("================================================")

# 執行主程式
if __name__ == "__main__":
    plot_and_save_individual_figs()