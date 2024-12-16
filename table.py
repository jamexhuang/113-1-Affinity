# ============================================
# AFFINITY的財務狀況模擬 By 311057012 黃子峻 (修改版)
# ============================================

from tabulate import tabulate

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
BASELINE_RPM = 65                         # 每千非訂閱用戶的廣告收入 (約2 USD)
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

# ============================================
# 函式區域
# ============================================

def calculate_mau(months_total, initial_growth_rate, final_growth_rate):
    mau_data = [0, 0]  # 前兩個月 MAU 為 0
    for month in range(2, months_total):
        # 凸性指數型下降
        ratio = (month - 2) / (months_total - 3)
        growth_rate = initial_growth_rate * ((final_growth_rate / initial_growth_rate) ** (ratio ** 2))
        prev_mau = mau_data[-1] if month > 2 else 1000
        new_mau = prev_mau * (1 + growth_rate)
        mau_data.append(new_mau)
    return mau_data

def calculate_revenues(mau_data, subscription_rate, monthly_subscription_price, annual_subscription_price, rpm):
    subscription_revenue, ad_revenue, monthly_revenue = [], [], []
    for month in range(len(mau_data)):
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

def calculate_cash_flow(monthly_revenue, personnel_cost_low, personnel_cost_high, operational_cost):
    personnel_costs = [personnel_cost_low if month < 2 else personnel_cost_high for month in range(len(monthly_revenue))]
    cash_flow = [monthly_revenue[month] - personnel_costs[month] - operational_cost for month in range(len(monthly_revenue))]
    cumulative_surplus = [sum(cash_flow[:month + 1]) for month in range(len(cash_flow))]
    breakeven_month = next((month + 1 for month in range(len(cumulative_surplus)) if cumulative_surplus[month] >= 0), None)
    return cash_flow, cumulative_surplus, breakeven_month

def process_scenario(scenario_name, initial_growth_rate, final_growth_rate, monthly_sub_price, annual_sub_price, subscription_rate, rpm, personnel_cost_low, personnel_cost_high, operational_cost):
    mau = calculate_mau(MONTHS_TOTAL, initial_growth_rate, final_growth_rate)
    sub_rev, ad_rev, monthly_rev = calculate_revenues(mau, subscription_rate, monthly_sub_price, annual_sub_price, rpm)
    cash_flow, cumulative_surplus, breakeven_month = calculate_cash_flow(monthly_rev, personnel_cost_low, personnel_cost_high, operational_cost)
    
    growth_rates = []
    for month in range(MONTHS_TOTAL):
        if month < 2:
            growth_rates.append(0)
        else:
            ratio = (month - 2) / (MONTHS_TOTAL - 3)
            rate = initial_growth_rate * ((final_growth_rate / initial_growth_rate) ** (ratio ** 2))
            growth_rates.append(rate * 100)
    
    cash_balance = [INITIAL_CAPITAL + cs for cs in cumulative_surplus]
    
    monthly_data = []
    for month in range(1, MONTHS_TOTAL + 1):
        data = {
            '月份': month,
            'MAU': f"{int(mau[month-1]):,}",
            '訂閱收入': f"{int(sub_rev[month-1]):,} TWD",
            '廣告收入': f"{int(ad_rev[month-1]):,} TWD",
            '總收入': f"{int(monthly_rev[month-1]):,} TWD",
            '現金流': f"{int(cash_flow[month-1]):,} TWD",
            '累積餘額': f"{int(cumulative_surplus[month-1]):,} TWD",
            '現金水位': f"{int(cash_balance[month-1]):,} TWD",
            '成長率 (%)': f"{growth_rates[month-1]:.2f}"
        }
        monthly_data.append(data)
    
    return {
        'scenario': scenario_name,
        'breakeven_month': breakeven_month,
        'final_cumulative_surplus': cumulative_surplus[-1] if cumulative_surplus else 0,
        'monthly_data': monthly_data
    }

# ============================================
# 主程式
# ============================================

def main():
    baseline_results = process_scenario(
        "Baseline",
        BASELINE_INITIAL_GROWTH_RATE,
        BASELINE_FINAL_GROWTH_RATE,
        BASELINE_MONTHLY_SUB_PRICE,
        BASELINE_ANNUAL_SUB_PRICE,
        BASELINE_SUBSCRIPTION_RATE,
        BASELINE_RPM,
        BASELINE_PERSONNEL_COST_LOW,
        BASELINE_PERSONNEL_COST_HIGH,
        BASELINE_OPERATIONAL_COST
    )
    
    conservative_results = process_scenario(
        "Conservative",
        CONSERVATIVE_INITIAL_GROWTH_RATE,
        CONSERVATIVE_FINAL_GROWTH_RATE,
        CONSERVATIVE_MONTHLY_SUB_PRICE,
        CONSERVATIVE_ANNUAL_SUB_PRICE,
        CONSERVATIVE_SUBSCRIPTION_RATE,
        CONSERVATIVE_RPM,
        CONSERVATIVE_PERSONNEL_COST_LOW,
        CONSERVATIVE_PERSONNEL_COST_HIGH,
        CONSERVATIVE_OPERATIONAL_COST
    )
    
    headers = ["月份", "MAU", "訂閱收入", "廣告收入", "總收入", "現金流", "累積餘額", "現金水位", "成長率 (%)"]
    
    print("\n==================== 財務摘要 ====================")
    print("\n--- Baseline Scenario ---")
    print(tabulate(baseline_results['monthly_data'], headers="keys", tablefmt="grid", stralign="right"))
    if baseline_results['breakeven_month']:
        print(f"\n有損益平衡點，於第 {baseline_results['breakeven_month']} 月達成。")
    else:
        print("\n無法在預設期間內達到損益平衡。")
    print(f"最終累積餘額: {baseline_results['final_cumulative_surplus']:,} TWD")
    
    print("\n--- Conservative Scenario ---")
    print(tabulate(conservative_results['monthly_data'], headers="keys", tablefmt="grid", stralign="right"))
    if conservative_results['breakeven_month']:
        print(f"\n有損益平衡點，於第 {conservative_results['breakeven_month']} 月達成。")
    else:
        print("\n無法在預設期間內達到損益平衡。")
    print(f"最終累積餘額: {conservative_results['final_cumulative_surplus']:,} TWD")
    print("\n================================================")

if __name__ == "__main__":
    main()