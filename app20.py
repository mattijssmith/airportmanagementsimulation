import streamlit as st
import pandas as pd
import random
import altair as alt

def scroll_to_top():
    """A helper function to inject JavaScript that scrolls the page to the top."""
    st.markdown(
        """
        <script>
            window.onload = function() {
                setTimeout(function() {
                    window.scrollTo(0, 0);
                }, 100);
            };
        </script>
        """,
        unsafe_allow_html=True
    )

class Airport:
    def __init__(self, initial_traffic, initial_equity, initial_assets, initial_opex_ratio, initial_asset_value, initial_cargo_tonnes):
        self.strategy = None
        self.year = 0
        self.traffic = initial_traffic
        self.cargo_tonnes = initial_cargo_tonnes
        self.capacity_pax = 15_000_000
        self.runway_capacity = 250_000
        self.runway_capacity_movements = 38
        self.pax_per_movement = 150
        self.peak_hour_factor = 0.15
        self.current_movements = (self.traffic / self.pax_per_movement / 365) * self.peak_hour_factor
        self.equity = initial_equity
        self.assets = initial_assets
        self.debt = 0
        self.loans = []
        self.opex_ratio = initial_opex_ratio
        self.asset_replacement_value = initial_asset_value
        self.marketing_budget_left = 5_000_000
        self.capex_projects = []
        self.capex_cash_outflow = 0
        self.depreciation = 0
        self.aeronautical_charge = 15
        self.cargo_charge_per_tonne = 100
        self.non_aero_spend_per_pax = 10
        self.non_aero_sqm = 5000
        self.revenue_aero = 0
        self.revenue_non_aero = 0
        self.revenue_cargo = 0
        self.opex = self.asset_replacement_value * self.opex_ratio
        self.interest_paid = 0
        self.profit_before_comp = 0
        self.profit_after_comp = 0
        self.retained_earnings = 0
        self.compensation = 0
        self.gdp_growth_factor = 1.0
        self.quality_factor = 1.0
        self.marketing_impact = 0.0
        self.charge_impact = 0.0
        self.opex_quality_impact = 0.0
        self.cost_impact = 0.0
        self.traffic_growth_rate = 0.0
        self.EBITDA = 0
        self.EBITDAR = 0
        self.concession_revenues = 0
        self.ancillary_revenues = 0
        self.total_opex = 0
        self.cash_balance = 50_000_000
        self.cfo = 0
        self.cfi = 0
        self.cff = 0
        self.unregulated_profit = 0
        self.regulated_profit = 0
        self.cargo_growth_rate = 0.0
        self.new_loans_this_year = 0

    def get_gearing(self):
        if self.equity == 0:
            return float('inf')
        return self.debt / self.equity

    def add_capex_project(self, project_name, cost, capacity_increase, lead_time, loan_amount):
        if project_name == 'Cargo Hangar':
            self.capex_projects.append({'name': project_name, 'cost': cost, 'capacity_increase': capacity_increase, 'lead_time': lead_time})
            st.info(f"Third-party project '{project_name}' initiated. It will be operational in {lead_time} year.")
            return True
        elif project_name == 'Non-Aero Retail Expansion':
            equity_portion = cost - loan_amount
            if self.cash_balance < equity_portion:
                st.error(f"Project '{project_name}' denied: Insufficient cash balance to fund the equity portion (${equity_portion:,.2f}). Current cash: ${self.cash_balance:,.2f}")
                return False
            self.capex_projects.append({'name': project_name, 'cost': cost, 'non_aero_sqm_increase': 1000, 'lead_time': lead_time})
            self.equity -= equity_portion
            self.capex_cash_outflow += cost
            if loan_amount > 0:
                self.take_loan(loan_amount)
            st.info(f"Project '{project_name}' initiated. It will be operational in {lead_time} year.")
            return True
        else:
            equity_portion = cost - loan_amount
            if self.cash_balance < equity_portion:
                st.error(f"Project '{project_name}' denied: Insufficient cash balance to fund the equity portion (${equity_portion:,.2f}). Current cash: ${self.cash_balance:,.2f}")
                return False
                
            self.capex_projects.append({'name': project_name, 'cost': cost, 'capacity_pax': capacity_increase, 'lead_time': lead_time})
            if loan_amount > 0:
                self.take_loan(loan_amount)
            self.equity -= equity_portion
            self.capex_cash_outflow += cost
            st.info(f"Project '{project_name}' is now operational in {lead_time} years.")
            return True

    def apply_marketing_impact(self, campaign_choice):
        marketing_options = {
            'a': {'cost': 1.8e6, 'impact': 0.015, 'type': 'aero', 'strategy_multipliers': {'Long Haul Hub': 0.8, 'Regional Hub': 1.0, 'Short Haul Spoke': 1.2, 'Long Haul Spoke': 1.0, 'Low-Cost Airport': 1.5, 'Cargo Airport': 0.5, 'Passenger and Cargo Hub': 1.0}},
            'b': {'cost': 2e6, 'impact': 0.02, 'type': 'aero', 'strategy_multipliers': {'Long Haul Hub': 1.5, 'Regional Hub': 0.8, 'Short Haul Spoke': 0.5, 'Long Haul Spoke': 1.2, 'Low-Cost Airport': 0.5, 'Cargo Airport': 0.3, 'Passenger and Cargo Hub': 1.3}},
            'c': {'cost': 5e6, 'impact': 0.04, 'type': 'aero', 'strategy_multipliers': {'Long Haul Hub': 0.7, 'Regional Hub': 1.0, 'Short Haul Spoke': 1.5, 'Long Haul Spoke': 0.9, 'Low-Cost Airport': 2.0, 'Cargo Airport': 0.1, 'Passenger and Cargo Hub': 0.8}},
            'd': {'cost': 2.5e6, 'impact': 0.03, 'type': 'aero', 'strategy_multipliers': {'Long Haul Hub': 1.2, 'Regional Hub': 1.1, 'Short Haul Spoke': 0.7, 'Long Haul Spoke': 1.3, 'Low-Cost Airport': 0.9, 'Cargo Airport': 0.8, 'Passenger and Cargo Hub': 1.0}},
            'e': {'cost': 1.25e6, 'impact': 0.01, 'type': 'aero', 'strategy_multipliers': {'Long Haul Hub': 0.5, 'Regional Hub': 0.8, 'Short Haul Spoke': 1.2, 'Long Haul Spoke': 0.9, 'Low-Cost Airport': 1.0, 'Cargo Airport': 1.5, 'Passenger and Cargo Hub': 1.2}},
            'f': {'cost': 1e6, 'impact': 0.1, 'type': 'non_aero', 'strategy_multipliers': {'Long Haul Hub': 1.5, 'Regional Hub': 1.2, 'Short Haul Spoke': 0.8, 'Long Haul Spoke': 1.0, 'Low-Cost Airport': 0.5, 'Cargo Airport': 0.1, 'Passenger and Cargo Hub': 1.5}},
            'g': {'cost': 2e6, 'impact': 0.2, 'type': 'non_aero', 'strategy_multipliers': {'Long Haul Hub': 2.0, 'Regional Hub': 1.5, 'Short Haul Spoke': 0.5, 'Long Haul Spoke': 1.2, 'Low-Cost Airport': 0.3, 'Cargo Airport': 0.1, 'Passenger and Cargo Hub': 1.8}}
        }
        
        cost = marketing_options[campaign_choice]['cost']
        if self.marketing_budget_left >= cost:
            self.marketing_budget_left -= cost
            
            impact_multiplier = marketing_options[campaign_choice]['strategy_multipliers'].get(self.strategy, 1.0)
            
            if marketing_options[campaign_choice]['type'] == 'aero':
                self.marketing_impact += marketing_options[campaign_choice]['impact'] * impact_multiplier
            elif marketing_options[campaign_choice]['type'] == 'non_aero':
                self.non_aero_spend_per_pax *= (1 + marketing_options[campaign_choice]['impact'] * impact_multiplier)

            st.success(f"Marketing campaign '{campaign_choice}' funded. Remaining budget: ${self.marketing_budget_left:,.2f}")
            return True
        else:
            st.warning(f"Insufficient budget to fund campaign '{campaign_choice}'. Remaining budget: ${self.marketing_budget_left:,.2f}")
            return False

    def take_loan(self, amount):
        if self.equity <= 0 or (self.debt + amount) / self.equity > 0.6:
            st.error("Loan denied: Gearing (debt to equity ratio) would exceed 0.6 or equity is zero.")
            return False
        self.debt += amount
        self.new_loans_this_year += amount
        self.loans.append({'amount': amount, 'original_amount': amount, 'years_remaining': 10, 'interest_rate': 0.045})
        st.success(f"Loan of ${amount:,.2f} taken. Total debt is now ${self.debt:,.2f}.")
        return True

    def update_for_new_year(self, gdp_growth, opex_change, aero_charge_change):
        # 1. Update Traffic
        self.gdp_growth_factor = 1 + (gdp_growth / 100)
        self.quality_factor = 1.0
        self.opex_quality_impact = 0.0
        self.cost_impact = 0.0
        self.cargo_growth_rate = 0.0
        
        strategy_params = {
            'Long Haul Hub': {'price_elasticity': 0.2, 'opex_quality_benchmark': 0.10, 'cost_penalty_multiplier': 1.5, 'quality_boost_multiplier': 6},
            'Regional Hub': {'price_elasticity': 0.4, 'opex_quality_benchmark': 0.0813, 'cost_penalty_multiplier': 2, 'quality_boost_multiplier': 5},
            'Short Haul Spoke': {'price_elasticity': 0.7, 'opex_quality_benchmark': 0.07, 'cost_penalty_multiplier': 3, 'quality_boost_multiplier': 4},
            'Long Haul Spoke': {'price_elasticity': 0.5, 'opex_quality_benchmark': 0.085, 'cost_penalty_multiplier': 2.5, 'quality_boost_multiplier': 5},
            'Low-Cost Airport': {'price_elasticity': 0.9, 'opex_quality_benchmark': 0.05, 'cost_penalty_multiplier': 4, 'quality_boost_multiplier': 2},
            'Cargo Airport': {'price_elasticity': 0.1, 'opex_quality_benchmark': 0.15, 'cost_penalty_multiplier': 1.0, 'quality_boost_multiplier': 8},
            'Passenger and Cargo Hub': {'price_elasticity': 0.3, 'opex_quality_benchmark': 0.12, 'cost_penalty_multiplier': 1.8, 'quality_boost_multiplier': 7}
        }
        
        params = strategy_params.get(self.strategy, strategy_params['Regional Hub'])

        # Check for completed projects
        self.depreciation = 0
        for project in list(self.capex_projects):
            project['lead_time'] -= 1
            if project['lead_time'] <= 0:
                if project['name'] == 'Cargo Hangar':
                    self.cargo_tonnes += project['capacity_increase']
                    st.info("Cargo Hangar is now operational, attracting more cargo traffic!")
                elif project['name'] == 'Non-Aero Retail Expansion':
                    self.non_aero_sqm += project['non_aero_sqm_increase']
                    self.asset_replacement_value += project['cost']
                    self.depreciation += project['cost'] / 25
                    st.info("Non-Aero Retail Expansion is now operational, increasing retail space!")
                else:
                    self.capacity_pax += project['capacity_pax']
                    self.asset_replacement_value += project['cost']
                    self.depreciation += project['cost'] / 25
                    st.info(f"Project '{project['name']}' is now operational!")
                self.capex_projects.remove(project)

        # Apply strategy-specific growth logic
        if self.strategy == 'Cargo Airport':
            # Cargo-specific logic
            cargo_growth_rate = (self.gdp_growth_factor - 1) * 0.5
            
            # Additional impact from completed projects
            for project in self.capex_projects:
                 if project['name'] == 'Cargo Hangar':
                    cargo_growth_rate += 0.05
            
            current_opex_ratio = self.opex / self.asset_replacement_value
            if current_opex_ratio < params['opex_quality_benchmark']:
                opex_quality_penalty = 1 - (params['opex_quality_benchmark'] - current_opex_ratio) * params['quality_boost_multiplier']
                cargo_growth_rate *= max(0.5, opex_quality_penalty)
            elif current_opex_ratio > params['opex_quality_benchmark']:
                opex_quality_boost = (current_opex_ratio - params['opex_quality_benchmark']) * params['quality_boost_multiplier']
                cargo_growth_rate += opex_quality_boost
                
                cost_penalty = (current_opex_ratio - params['opex_quality_benchmark']) * params['cost_penalty_multiplier']
                cargo_growth_rate -= cost_penalty
            
            self.cargo_growth_rate = cargo_growth_rate + self.marketing_impact
            self.cargo_tonnes *= (1 + self.cargo_growth_rate)
            self.traffic = self.cargo_tonnes * 0.001
        elif self.strategy == 'Passenger and Cargo Hub':
            # Blended Passenger and Cargo logic
            # Passenger growth
            terminal_capacity_utilization = self.traffic / self.capacity_pax
            if terminal_capacity_utilization > 0.8:
                self.quality_factor *= max(0.5, 1 - (terminal_capacity_utilization - 0.8) * 2)
            
            self.current_movements = (self.traffic / self.pax_per_movement / 365) * self.peak_hour_factor
            runway_utilization = self.current_movements / self.runway_capacity_movements
            if runway_utilization > 0.8:
                self.quality_factor *= max(0.5, 1 - (runway_utilization - 0.8) * 2)

            self.quality_factor = max(0.5, min(1.5, self.quality_factor))

            current_opex_ratio = self.opex / self.asset_replacement_value
            if current_opex_ratio < params['opex_quality_benchmark']:
                opex_quality_penalty = 1 - (params['opex_quality_benchmark'] - current_opex_ratio) * params['quality_boost_multiplier']
                self.quality_factor *= max(0.5, opex_quality_penalty)
                self.opex_quality_impact = self.quality_factor - 1
            elif current_opex_ratio > params['opex_quality_benchmark']:
                opex_quality_boost = (current_opex_ratio - params['opex_quality_benchmark']) * params['quality_boost_multiplier']
                self.quality_factor *= 1 + opex_quality_boost
                self.opex_quality_impact = opex_quality_boost
                
                cost_penalty = (current_opex_ratio - params['opex_quality_benchmark']) * params['cost_penalty_multiplier']
                self.cost_impact = cost_penalty
            
            aero_charge_elasticity = params['price_elasticity']
            self.charge_impact = -(aero_charge_change / 100) * aero_charge_elasticity
            self.traffic_growth_rate = (self.gdp_growth_factor - 1) + (self.quality_factor - 1) + self.marketing_impact + self.charge_impact - self.cost_impact
            new_traffic = self.traffic * (1 + self.traffic_growth_rate)
            self.traffic = min(new_traffic, self.capacity_pax * 1.5)

            # Cargo growth
            cargo_growth_rate_base = (self.gdp_growth_factor - 1) * 0.5
            for project in self.capex_projects:
                 if project['name'] == 'Cargo Hangar':
                    cargo_growth_rate_base += 0.05
            
            cargo_growth_rate_quality = (self.quality_factor - 1) * 0.5
            self.cargo_growth_rate = cargo_growth_rate_base + cargo_growth_rate_quality + self.marketing_impact
            self.cargo_tonnes *= (1 + self.cargo_growth_rate)
        else:
            # Passenger-only logic (existing strategies)
            terminal_capacity_utilization = self.traffic / self.capacity_pax
            if terminal_capacity_utilization > 0.8:
                self.quality_factor *= max(0.5, 1 - (terminal_capacity_utilization - 0.8) * 2)
            
            self.current_movements = (self.traffic / self.pax_per_movement / 365) * self.peak_hour_factor
            runway_utilization = self.current_movements / self.runway_capacity_movements
            if runway_utilization > 0.8:
                self.quality_factor *= max(0.5, 1 - (runway_utilization - 0.8) * 2)

            self.quality_factor = max(0.5, min(1.5, self.quality_factor))

            current_opex_ratio = self.opex / self.asset_replacement_value
            if current_opex_ratio < params['opex_quality_benchmark']:
                opex_quality_penalty = 1 - (params['opex_quality_benchmark'] - current_opex_ratio) * params['quality_boost_multiplier']
                self.quality_factor *= max(0.5, opex_quality_penalty)
                self.opex_quality_impact = self.quality_factor - 1
            elif current_opex_ratio > params['opex_quality_benchmark']:
                opex_quality_boost = (current_opex_ratio - params['opex_quality_benchmark']) * params['quality_boost_multiplier']
                self.quality_factor *= 1 + opex_quality_boost
                self.opex_quality_impact = opex_quality_boost
            
                cost_penalty = (current_opex_ratio - params['opex_quality_benchmark']) * params['cost_penalty_multiplier']
                self.cost_impact = cost_penalty

            aero_charge_elasticity = params['price_elasticity']
            self.charge_impact = -(aero_charge_change / 100) * aero_charge_elasticity

            self.traffic_growth_rate = (self.gdp_growth_factor - 1) + (self.quality_factor - 1) + self.marketing_impact + self.charge_impact - self.cost_impact
            new_traffic = self.traffic * (1 + self.traffic_growth_rate)
            self.traffic = min(new_traffic, self.capacity_pax * 1.5)
            
        # 3. Calculate financial metrics
        self.aeronautical_charge *= (1 + aero_charge_change/100)

        # New Non-Aero Revenue calculation
        self.revenue_non_aero = self.traffic * (self.non_aero_spend_per_pax) * (self.non_aero_sqm / 5000)

        self.revenue_aero = self.traffic * self.aeronautical_charge
        self.revenue_cargo = self.cargo_tonnes * self.cargo_charge_per_tonne

        total_revenue = self.revenue_aero + self.revenue_non_aero + self.revenue_cargo
        
        self.opex *= (1 + opex_change/100)
        self.total_opex = self.opex

        self.concession_revenues = self.revenue_non_aero * 0.8 
        self.ancillary_revenues = self.revenue_non_aero * 0.2  

        self.EBITDA = total_revenue - self.total_opex
        self.EBITDAR = self.EBITDA + self.ancillary_revenues 
        
        self.interest_paid = 0
        loan_principal_repayment = 0
        loans_to_keep = []
        for loan in self.loans:
            self.interest_paid += loan['amount'] * loan['interest_rate']
            principal_payment = loan['original_amount'] / 10
            loan['amount'] -= principal_payment
            loan_principal_repayment += principal_payment
            loan['years_remaining'] -= 1
            if loan['years_remaining'] > 0:
                loans_to_keep.append(loan)
        self.loans = loans_to_keep
        self.debt = sum(l['amount'] for l in self.loans)

        # Calculate regulated profit for compensation
        if self.strategy == 'Cargo Airport':
            regulated_revenue = self.revenue_cargo
        elif self.strategy == 'Passenger and Cargo Hub':
            regulated_revenue = self.revenue_aero + self.revenue_cargo
        else:
            regulated_revenue = self.revenue_aero

        total_revenue_for_allocation = self.revenue_aero + self.revenue_non_aero + self.revenue_cargo
        if total_revenue_for_allocation > 0:
            regulated_revenue_share = regulated_revenue / total_revenue_for_allocation
        else:
            regulated_revenue_share = 0

        allocated_opex = self.opex * regulated_revenue_share
        allocated_depreciation = self.depreciation * regulated_revenue_share
        allocated_interest = self.interest_paid * regulated_revenue_share
        allocated_equity = self.equity * regulated_revenue_share

        self.regulated_profit = regulated_revenue - allocated_opex - allocated_depreciation - allocated_interest
        self.unregulated_profit = (total_revenue - regulated_revenue) - (self.opex - allocated_opex) - (self.depreciation - allocated_depreciation) - (self.interest_paid - allocated_interest)

        self.compensation = 0
        if allocated_equity > 0:
            roe_regulated = (self.regulated_profit / allocated_equity)
            if roe_regulated > 0.10:
                excess_profit = self.regulated_profit - (allocated_equity * 0.10)
                self.compensation = excess_profit
                st.success(f"Economic Regulation Compensation paid: ${self.compensation:,.2f}")
        
        self.profit_before_comp = self.regulated_profit + self.unregulated_profit
        self.profit_after_comp = self.profit_before_comp - self.compensation
        self.retained_earnings += self.profit_after_comp
        self.equity += self.profit_after_comp

        # 4. Calculate Cash Flow
        self.cfo = self.EBITDA - self.compensation
        self.cfi = -self.capex_cash_outflow
        
        self.cff = self.new_loans_this_year - loan_principal_repayment

        # Re-calculating cash balance with correct cff
        self.cash_balance += self.cfo + self.cfi + self.cff
        
        self.capex_cash_outflow = 0
        self.new_loans_this_year = 0
        self.marketing_budget_left = 5_000_000
        self.marketing_impact = 0.0
        
    def display_metrics(self):
        roe = (self.profit_after_comp / self.equity) * 100 if self.equity > 0 else 0
        
        st.subheader("Airport Performance Metrics")
        st.write(f"Year: {st.session_state.current_year}")

        if self.strategy in ['Cargo Airport', 'Passenger and Cargo Hub']:
            st.write(f"Annual Cargo: {self.cargo_tonnes:,.0f} tonnes")
            st.write(f"Cargo Growth: {self.cargo_growth_rate * 100:.2f}%")

        if self.strategy != 'Cargo Airport':
            terminal_capacity_utilization = (self.traffic / self.capacity_pax) * 100
            runway_capacity_utilization = (self.current_movements / self.runway_capacity_movements) * 100
            st.write(f"Annual Traffic: {self.traffic:,.0f} passengers")
            st.write(f"Traffic Growth: {self.traffic_growth_rate * 100:.2f}%")
            st.write(f"Terminal Capacity: {self.capacity_pax:,.0f} passengers")
            st.write(f"Terminal Capacity Utilization: {terminal_capacity_utilization:.2f}%")
            st.write(f"Runway Capacity: {self.runway_capacity_movements:,.0f} movements per hour")
            st.write(f"Current Movements per peak hour: {self.current_movements:.2f}")
            st.write(f"Runway Capacity Utilization (Peak Hour): {runway_capacity_utilization:.2f}%")


        st.write(f"Quality Impact on Traffic: {(self.quality_factor-1)*100:.2f}%")
        st.write(f"Aeronautical Charges Impact on Traffic: {self.charge_impact * 100:.2f}%")
        st.write(f"Cost Impact on Traffic: {self.cost_impact * -100:.2f}%")


        st.subheader("Financial Metrics")
        if self.strategy == 'Cargo Airport':
            st.write(f"Revenues (Cargo): ${self.revenue_cargo:,.2f}")
            st.write(f"Revenues (Non-Aero): ${self.revenue_non_aero:,.2f}")
            st.write(f"Total Revenues: ${self.revenue_cargo + self.revenue_non_aero:,.2f}")
        elif self.strategy == 'Passenger and Cargo Hub':
            st.write(f"Revenues (Aero): ${self.revenue_aero:,.2f}")
            st.write(f"Revenues (Cargo): ${self.revenue_cargo:,.2f}")
            st.write(f"Revenues (Non-Aero): ${self.revenue_non_aero:,.2f}")
            st.write(f"Total Revenues: ${self.revenue_aero + self.revenue_cargo + self.revenue_non_aero:,.2f}")
        else:
            st.write(f"Revenues (Aero): ${self.revenue_aero:,.2f}")
            st.write(f"Revenues (Non-Aero): ${self.revenue_non_aero:,.2f}")
            st.write(f"Total Revenues: ${self.revenue_aero + self.revenue_non_aero:,.2f}")
        
        st.write(f"OPEX: ${self.opex:,.2f}")
        st.write(f"OPEX % of Asset Value: {(self.opex / self.asset_replacement_value) * 100:.2f}%")
        
        st.write(f"Profit (Regulated Business): ${self.regulated_profit:,.2f}")
        st.write(f"Profit (Unregulated Business): ${self.unregulated_profit:,.2f}")
        st.write(f"Total Profit (Pre-Compensation): ${self.profit_before_comp:,.2f}")
        st.write(f"Economic Regulation Compensation: ${self.compensation:,.2f}")
        st.write(f"Profit (Post-Compensation): ${self.profit_after_comp:,.2f}")
        
        st.write(f"Return on Equity (ROE): {roe:.2f}%")
        st.write(f"Gearing (Debt/Equity): {self.get_gearing():.2f}")

        st.subheader("Cash Flow Statement")
        st.write(f"Cash Balance (Start of Year): ${self.cash_balance - (self.cfo + self.cfi + self.cff):,.2f}")
        st.write(f"Cash Flow from Operations (CFO): ${self.cfo:,.2f}")
        st.write(f"Cash Flow from Investing (CFI): ${self.cfi:,.2f}")
        st.write(f"Cash Flow from Financing (CFF): ${self.cff:,.2f}")
        st.write(f"Net Change in Cash: ${self.cfo + self.cfi + self.cff:,.2f}")
        st.write(f"Cash Balance (End of Year): ${self.cash_balance:,.2f}")

# Main Streamlit application logic
st.title("Airport Management Simulation 🛫")

if 'airport' not in st.session_state:
    st.session_state.airport = Airport(initial_traffic=10_000_000, initial_equity=500_000_000, initial_assets=500_000_000, initial_opex_ratio=0.1, initial_asset_value=1_000_000_000, initial_cargo_tonnes=500_000)

if 'gdp_data' not in st.session_state:
    st.session_state.gdp_data = {
        1: 2.0, 2: 2.5, 3: 1.8, 4: 3.0, 5: 2.2,
        6: 2.8, 7: 1.5, 8: 2.0, 9: 2.5, 10: 2.3,
        11: 2.1, 12: 1.9, 13: 2.6, 14: 2.4, 15: 2.7,
        16: 2.0, 17: 2.2, 18: 2.5, 19: 2.1, 20: 2.3
    }

if 'history' not in st.session_state:
    st.session_state.history = []

if 'simulate_clicked' not in st.session_state:
    st.session_state.simulate_clicked = False

if 'current_year' not in st.session_state:
    st.session_state.current_year = 0

def advance_year():
    st.session_state.simulate_clicked = False
    st.session_state.current_year += 1
    st.rerun()
    scroll_to_top()

if st.session_state.airport.strategy is None:
    st.header("Current Airport Status (Initial Year)")
    terminal_utilization = (st.session_state.airport.traffic / st.session_state.airport.capacity_pax) * 100
    initial_opex_percent = (st.session_state.airport.opex / st.session_state.airport.asset_replacement_value) * 100
    initial_runway_utilization = (st.session_state.airport.current_movements / st.session_state.airport.runway_capacity_movements) * 100

    st.write(f"Current Passenger Capacity: {st.session_state.airport.capacity_pax:,.0f} passengers")
    st.write(f"Current Number of Passengers: {st.session_state.airport.traffic:,.0f} passengers")
    st.write(f"Current Number of Cargo Tonnes: {st.session_state.airport.cargo_tonnes:,.0f} tonnes")
    st.write(f"Current Terminal Capacity Utilization: {terminal_utilization:.2f}%")
    st.write(f"Current Runway Capacity: {st.session_state.airport.runway_capacity_movements:,.0f} movements per hour")
    st.write(f"Current Movements per peak hour: {st.session_state.airport.current_movements:.2f}")
    st.write(f"Current Runway Capacity Utilization (Peak Hour): {initial_runway_utilization:.2f}%")
    st.write(f"Current OPEX: ${st.session_state.airport.opex:,.2f}")
    st.write(f"Current OPEX as % of Asset Value: {initial_opex_percent:.2f}%")
    st.write(f"Current Spend per Passenger (Non-Aero): ${st.session_state.airport.non_aero_spend_per_pax:,.2f}")

    st.header("Year 1: Strategic Planning")
    strategy_map = {'Long Haul Hub': 'a', 'Regional Hub': 'b', 'Short Haul Spoke': 'c', 'Long Haul Spoke': 'd', 'Low-Cost Airport': 'e', 'Cargo Airport': 'f', 'Passenger and Cargo Hub': 'g'}
    strategy_choice = st.selectbox("Choose your airport's strategy:", list(strategy_map.keys()))

    if st.button("Start Simulation"):
        st.session_state.airport.strategy = strategy_choice
        st.session_state.current_year = 1
        st.session_state.run_simulation_flag = True
        st.session_state.simulate_clicked = False
        st.rerun()
    scroll_to_top()

elif st.session_state.current_year > 10:
    st.balloons()
    st.header("Simulation Complete!")
    st.write("You have reached the end of the 10-year simulation. Rerun the app to start over.")
    scroll_to_top()
else:
    if st.session_state.simulate_clicked:
        
        # Display Input Summary
        st.header(f"Results for Year {st.session_state.current_year}")
        st.subheader("Input Summary")
        
        st.write(f"**CAPEX Project:** {st.session_state.get('selected_project_display', 'None')}")
        if st.session_state.get('selected_project_display', 'None') != 'None':
            st.write(f"**Lead Time:** {st.session_state.get('lead_time_display', 0)} years")
            st.write(f"**Project Available:** Year {st.session_state.get('project_availability_year_display', st.session_state.current_year)}")
        if st.session_state.get('loan_amount_display', 0) > 0:
            st.write(f"**Loan Amount:** ${st.session_state.get('loan_amount_display', 0):,.2f}")
        st.write(f"**Marketing Campaigns:** {', '.join(st.session_state.get('selected_campaigns_display', ['None']))}")
        st.write(f"**OPEX Change:** {st.session_state.get('opex_change_display', 0.0):.2f}%")
        st.write(f"**Airport Charges Change:** {st.session_state.get('aero_charge_change_display', 0.0):.2f}%")

        st.markdown("---")
        st.subheader("Actual Economic Factors")
        st.write(f"**Actual GDP Growth:** {st.session_state.get('gdp_growth_display', 0.0)}%")
        st.markdown("---")

        st.session_state.airport.display_metrics()

        # Display Summary Tables and Graphs after every year
        st.markdown("---")
        st.header(f"Simulation Overview (Years 1 to {st.session_state.current_year})")

        history_df = pd.DataFrame(st.session_state.history)

        # Separate Decision Table
        st.subheader("Summary of Decisions")
        decisions_df = history_df[['Year', 'CAPEX Project', 'Lead Time', 'Project Available in Year', 'Loan Amount', 'Marketing Campaigns', 'OPEX Change (%)', 'Airport Charges Change (%)']].set_index('Year')
        st.dataframe(decisions_df.style.format({
            'Lead Time': '{:,.0f}',
            'Project Available in Year': '{:,.0f}',
            'Loan Amount': '${:,.2f}',
            'OPEX Change (%)': '{:.2f}%',
            'Airport Charges Change (%)': '{:.2f}%'
        }))

        # Separate Metrics Table
        st.subheader("Summary of Key Metrics")
        metrics_df = history_df[['Year', 'Traffic', 'Capacity', 'Terminal Utilization', 'Runway Utilization', 'Profit', 'Cash Balance (End of Year)', 'Cash Flow from Operations (CFO)', 'Cash Flow from Investing (CFI)', 'Cash Flow from Financing (CFF)', 'Quality Impact on Traffic (%)', 'Aero Charges Impact on Traffic (%)', 'Cost Impact on Traffic (%)']].set_index('Year')
        st.dataframe(metrics_df.style.format({
            'Traffic': '{:,.0f}',
            'Capacity': '{:,.0f}',
            'Terminal Utilization': '{:.2f}%',
            'Runway Utilization': '{:.2f}%',
            'Profit': '${:,.2f}',
            'Cash Balance (End of Year)': '${:,.2f}',
            'Cash Flow from Operations (CFO)': '${:,.2f}',
            'Cash Flow from Investing (CFI)': '${:,.2f}',
            'Cash Flow from Financing (CFF)': '${:,.2f}',
            'Quality Impact on Traffic (%)': '{:.2f}%',
            'Aero Charges Impact on Traffic (%)': '{:.2f}%',
            'Cost Impact on Traffic (%)': '{:.2f}%'
        }))

        # Display Graphs
        st.subheader("Simulation Graphs")

        # 1. Traffic Development
        st.line_chart(history_df, x='Year', y=['Traffic', 'Capacity'])

        # 2. Capacity Utilisation - Line Chart
        st.subheader("Capacity Utilisation")
        utilization_df = history_df[['Year', 'Terminal Utilization', 'Runway Utilization']].melt('Year', var_name='Metric', value_name='Utilization (%)')
        chart = alt.Chart(utilization_df).mark_line().encode(
            x=alt.X('Year:O', axis=alt.Axis(title='Year')),
            y=alt.Y('Utilization (%):Q', axis=alt.Axis(title='Utilization (%)')),
            color='Metric:N',
            tooltip=['Year', 'Metric', alt.Tooltip('Utilization (%):Q', format='.2f')]
        ).properties(
            title="Capacity Utilisation Over Time"
        )
        st.altair_chart(chart, use_container_width=True)

        # 3. Profit and Cash Flow
        st.subheader("Profit and Cash Flow")
        financial_df = history_df[['Year', 'Profit', 'Cash Balance (End of Year)']].set_index('Year')
        st.line_chart(financial_df)

        # 4. Traffic Impact Analysis - Line Chart
        st.subheader("Traffic Impact Analysis")
        impact_df = history_df[['Year', 'Quality Impact on Traffic (%)', 'Aero Charges Impact on Traffic (%)', 'Cost Impact on Traffic (%)']].melt('Year', var_name='Metric', value_name='Impact (%)')
        impact_chart = alt.Chart(impact_df).mark_line().encode(
            x=alt.X('Year:O', axis=alt.Axis(title='Year')),
            y=alt.Y('Impact (%):Q', axis=alt.Axis(title='Impact (%)')),
            color='Metric:N',
            tooltip=['Year', 'Metric', alt.Tooltip('Impact (%):Q', format='.2f')]
        ).properties(
            title="Traffic Impact Analysis Over Time"
        )
        st.altair_chart(impact_chart, use_container_width=True)
        
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        if st.button("Advance to Next Year"):
            advance_year()
        scroll_to_top()
    else:
        st.session_state.airport.year = st.session_state.current_year
        st.header(f"Decisions for Year {st.session_state.current_year}")
        gdp_growth = st.session_state.gdp_data.get(st.session_state.current_year, 2.0)
        st.write(f"Predicted GDP Growth for the year: **{gdp_growth}%**")

        st.subheader("CAPEX Projects")
        project_options = {
            'None': 0, 'New Terminal': 1, 'Expand Runway': 2, 'Cargo Hangar': 3, 'Non-Aero Retail Expansion': 4
        }
        selected_project = st.selectbox("Select a project:", list(project_options.keys()))

        lead_time = 0
        project_availability_year = 0
        if selected_project in ['New Terminal', 'Expand Runway']:
            lead_time = 3
            project_availability_year = st.session_state.current_year + lead_time
        elif selected_project in ['Cargo Hangar', 'Non-Aero Retail Expansion']:
            lead_time = 1
            project_availability_year = st.session_state.current_year + lead_time
        
        if selected_project != 'None':
            st.write(f"**Lead Time:** {lead_time} years")
            st.write(f"**Project Available:** Year {project_availability_year}")

        loan_amount = 0
        if selected_project in ['New Terminal', 'Expand Runway', 'Non-Aero Retail Expansion']:
            cost_options = {'New Terminal': 150_000_000, 'Expand Runway': 250_000_000, 'Non-Aero Retail Expansion': 50_000_000}
            cost = cost_options.get(selected_project, 0)
            loan_amount = st.number_input(f"Enter the loan amount for {selected_project} (max {cost:,.0f}):", max_value=float(cost), step=10000.0)

        st.subheader("Marketing Campaigns")
        st.write(f"Remaining budget: ${st.session_state.airport.marketing_budget_left:,.2f}")
        
        marketing_options = {
            'a. General Awareness (€1.8M)': 'a',
            'b. Long Haul Promotion (€2M)': 'b',
            'c. Charges Discount (€5M)': 'c',
            'd. Attract New Airlines (€2.5M)': 'd',
            'e. General Aviation Promo (€1.25M)': 'e',
            'f. Retail Promotion (€1M)': 'f',
            'g. Gourmet Food & Beverage Launch (€2M)': 'g'
        }
        selected_campaigns = st.multiselect(
            "Select campaigns to fund (Max €5M every two years):",
            list(marketing_options.keys())
        )

        st.subheader("Annual Operational Changes")
        opex_change = st.number_input("Enter OPEX change (% over previous year):", value=0.0)
        aero_charge_change = st.number_input("Enter Airport Charges change (% over previous year):", value=0.0)

        if st.button("Simulate Year"):
            
            # Store inputs in session state before simulation
            st.session_state['selected_project_display'] = selected_project
            st.session_state['loan_amount_display'] = loan_amount
            st.session_state['selected_campaigns_display'] = selected_campaigns
            st.session_state['opex_change_display'] = opex_change
            st.session_state['aero_charge_change_display'] = aero_charge_change
            st.session_state['gdp_growth_display'] = gdp_growth
            st.session_state['lead_time_display'] = lead_time
            st.session_state['project_availability_year_display'] = project_availability_year

            if selected_project != 'None':
                project_name = selected_project
                
                # Corrected logic for cost and capacity increase
                if project_name == 'New Terminal':
                    cost = 150_000_000
                    capacity_increase = 2_000_000
                elif project_name == 'Expand Runway':
                    cost = 250_000_000
                    capacity_increase = 3_000_000
                elif project_name == 'Cargo Hangar':
                    cost = 45_000_000
                    capacity_increase = 200_000
                elif project_name == 'Non-Aero Retail Expansion':
                    cost = 50_000_000
                    capacity_increase = 0  # No passenger capacity increase
                else:
                    cost = 0
                    capacity_increase = 0

                st.session_state.airport.add_capex_project(project_name, cost, capacity_increase, lead_time, loan_amount)

            for campaign_label in selected_campaigns:
                campaign_code = marketing_options[campaign_label]
                st.session_state.airport.apply_marketing_impact(campaign_code)
            
            # The order is changed here: update the year's data, then store it, then set the flag.
            # The year will be incremented within update_for_new_year.
            st.session_state.airport.update_for_new_year(gdp_growth, opex_change, aero_charge_change)

            # Store historical data
            year_data = {
                'Year': st.session_state.current_year,
                'CAPEX Project': st.session_state.get('selected_project_display', 'None'),
                'Lead Time': lead_time,
                'Project Available in Year': project_availability_year,
                'Loan Amount': st.session_state.get('loan_amount_display', 0),
                'Marketing Campaigns': ', '.join(st.session_state.get('selected_campaigns_display', ['None'])),
                'OPEX Change (%)': st.session_state.get('opex_change_display', 0.0),
                'Airport Charges Change (%)': st.session_state.get('aero_charge_change_display', 0.0),
                'Traffic': st.session_state.airport.traffic,
                'Capacity': st.session_state.airport.capacity_pax,
                'Terminal Utilization': (st.session_state.airport.traffic / st.session_state.airport.capacity_pax) * 100,
                'Runway Utilization': (st.session_state.airport.current_movements / st.session_state.airport.runway_capacity_movements) * 100,
                'Profit': st.session_state.airport.profit_after_comp,
                'Cash Balance (End of Year)': st.session_state.airport.cash_balance,
                'Cash Flow from Operations (CFO)': st.session_state.airport.cfo,
                'Cash Flow from Investing (CFI)': st.session_state.airport.cfi,
                'Cash Flow from Financing (CFF)': st.session_state.airport.cff,
                'Quality Impact on Traffic (%)': (st.session_state.airport.quality_factor-1)*100,
                'Aero Charges Impact on Traffic (%)': st.session_state.airport.charge_impact * 100,
                'Cost Impact on Traffic (%)': st.session_state.airport.cost_impact * -100,
            }
            st.session_state.history.append(year_data)
            
            st.session_state.simulate_clicked = True
            st.rerun()
        scroll_to_top()