import streamlit as st
import pandas as pd
import random
import altair as alt
import yaml
from yaml.loader import SafeLoader
import pathlib
import streamlit_authenticator as stauth

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
        self.marketing_expense = 0.0
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
        # -----------------------------
        # OPEX calculation mode toggle
        # -----------------------------
        self.opex_mode = "ratio"  # default; can be "structured"

        # --- Structured OPEX parameters (Mid-size EU Mixed defaults) ---
        self.hr_base = 28_000_000
        self.hr_per_pax = 0.55
        self.hr_per_movement = 140
        self.wage_growth = 0.025

        self.maint_pct_arv = 0.017
        self.maint_per_movement = 22

        self.kwh_per_pax = 2.2
        self.kwh_per_sqm = 230.0
        self.price_per_kwh = 0.18
        self.energy_intensity_factor = 1.0

        self.sec_base = 16_000_000
        self.sec_per_pax = 0.32
        self.sec_per_movement = 55

        self.it_base = 6_500_000
        self.it_per_pax = 0.11
        self.it_pct_arv = 0.002

        self.ins_pct_arv = 0.0016
        self.ins_pct_revenue = 0.0018

        self.co2_per_pax_kg = 0.6
        self.carbon_price = 80.0
        self.noise_per_movement = 6.0

        self.concession_fee_pct = 0.02

        self.handling_per_movement = 25

        self.other_base = 4_500_000
        self.inflation_assumption = 0.02

        self.shock_prob = 0.03
        self.shock_amount = 6_000_000


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

            
            self.marketing_expense = getattr(self, 'marketing_expense', 0.0) + cost
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
            cargo_growth_rate = (self.gdp_growth_factor - 1) * 0.5
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
        if self.opex_mode == "ratio":
            # Legacy OPEX calculation
            self.aeronautical_charge *= (1 + aero_charge_change/100)
            self.revenue_non_aero = self.traffic * (self.non_aero_spend_per_pax) * (self.non_aero_sqm / 5000)
            self.revenue_aero = self.traffic * self.aeronautical_charge
            self.revenue_cargo = self.cargo_tonnes * self.cargo_charge_per_tonne
            total_revenue = self.revenue_aero + self.revenue_non_aero + self.revenue_cargo
            self.opex *= (1 + opex_change/100)
            self.total_opex = self.opex + getattr(self, 'marketing_expense', 0.0)
        elif self.opex_mode == "structured":
            # Structured OPEX calculation
            self.aeronautical_charge *= (1 + aero_charge_change/100)
            self.revenue_non_aero = self.traffic * (self.non_aero_spend_per_pax) * (self.non_aero_sqm / 5000)
            self.revenue_aero = self.traffic * self.aeronautical_charge
            self.revenue_cargo = self.cargo_tonnes * self.cargo_charge_per_tonne
            total_revenue = self.revenue_aero + self.revenue_non_aero + self.revenue_cargo

            P_t = self.traffic
            ARV_t = self.asset_replacement_value
            SQM_t = self.non_aero_sqm
            pax_per_flight = max(1, self.pax_per_movement)
            flights_per_year = P_t / pax_per_flight
            M_t = flights_per_year

            wage_growth_t = self.wage_growth + (opex_change/100)*0.5
            inflation_t = self.inflation_assumption + (opex_change/100)*0.5
            price_kWh_t = self.price_per_kwh * (1 + (opex_change/100)*0.8)

            StaffCost = (self.hr_base + self.hr_per_pax * P_t + self.hr_per_movement * M_t) * (1 + wage_growth_t)
            MaintCost = self.maint_pct_arv * ARV_t + self.maint_per_movement * M_t
            kwh_terminal = self.kwh_per_pax * P_t * self.energy_intensity_factor
            kwh_retail = SQM_t * self.kwh_per_sqm
            EnergyCost = (kwh_terminal + kwh_retail) * price_kWh_t
            SecComp = self.sec_base + self.sec_per_pax * P_t + self.sec_per_movement * M_t
            ITCost = self.it_base + self.it_per_pax * P_t + self.it_pct_arv * ARV_t
            Insurance = self.ins_pct_arv * ARV_t + self.ins_pct_revenue * total_revenue
            tonnes_CO2 = (self.co2_per_pax_kg * P_t) / 1000.0
            Env = tonnes_CO2 * self.carbon_price + self.noise_per_movement * M_t
            ConcessionFee = self.concession_fee_pct * total_revenue
            HandlingSupport = self.handling_per_movement * M_t
            Other = self.other_base * (1 + inflation_t)
            Shock = 0.0
            if random.random() < self.shock_prob:
                Shock = self.shock_amount
                st.warning(f"Extraordinary cost shock incurred this year: €{Shock:,.0f}")
            OPEX_struct = StaffCost + MaintCost + EnergyCost + SecComp + ITCost + Insurance + Env + ConcessionFee + HandlingSupport + Other + Shock

            # Apply global scenario effects after calculating cost drivers
            scenario = getattr(st.session_state, "scenario", "Baseline")
            if scenario == "High Energy Crisis":
                if self.year <= 3:  # first 3 years
                    EnergyCost *= 2.0
                    self.opex *= 2.0
            elif scenario == "High Inflation":
                inflation_t += 0.03
            elif scenario == "Carbon Tax Surge":
                self.carbon_price *= 1.10

            self.opex = OPEX_struct
            self.total_opex = self.opex + getattr(self, 'marketing_expense', 0.0)

        self.aeronautical_charge *= (1 + aero_charge_change/100)

        # New Non-Aero Revenue calculation
        self.revenue_non_aero = self.traffic * (self.non_aero_spend_per_pax) * (self.non_aero_sqm / 5000)

        self.revenue_aero = self.traffic * self.aeronautical_charge
        self.revenue_cargo = self.cargo_tonnes * self.cargo_charge_per_tonne

        total_revenue = self.revenue_aero + self.revenue_non_aero + self.revenue_cargo

        self.opex *= (1 + opex_change/100)
        self.total_opex = self.opex + getattr(self, 'marketing_expense', 0.0)

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
        self.cfo = self.EBITDA - self.compensation - self.interest_paid
        self.cfi = -self.capex_cash_outflow

        self.cff = self.new_loans_this_year - loan_principal_repayment

        # Re-calculating cash balance with correct cff
        self.cash_balance += self.cfo + self.cfi + self.cff

        

        # Reset yearly marketing expense
        self.marketing_expense = 0.0
        self.capex_cash_outflow = 0
        self.new_loans_this_year = 0
        # -----------------------------
        # OPEX calculation mode toggle
        # -----------------------------
        self.opex_mode = "ratio"  # default; can be "structured"

        # --- Structured OPEX parameters (Mid-size EU Mixed defaults) ---
        self.hr_base = 28_000_000
        self.hr_per_pax = 0.55
        self.hr_per_movement = 140
        self.wage_growth = 0.025

        self.maint_pct_arv = 0.017
        self.maint_per_movement = 22

        self.kwh_per_pax = 2.2
        self.kwh_per_sqm = 230.0
        self.price_per_kwh = 0.18
        self.energy_intensity_factor = 1.0

        self.sec_base = 16_000_000
        self.sec_per_pax = 0.32
        self.sec_per_movement = 55

        self.it_base = 6_500_000
        self.it_per_pax = 0.11
        self.it_pct_arv = 0.002

        self.ins_pct_arv = 0.0016
        self.ins_pct_revenue = 0.0018

        self.co2_per_pax_kg = 0.6
        self.carbon_price = 80.0
        self.noise_per_movement = 6.0

        self.concession_fee_pct = 0.02

        self.handling_per_movement = 25

        self.other_base = 4_500_000
        self.inflation_assumption = 0.02

        self.shock_prob = 0.03
        self.shock_amount = 6_000_000

        self.marketing_budget_left = 5_000_000
        self.marketing_impact = 0.0


    def calibrate_costs(self, target_opex_per_pax=20.0, target_opex_pct_arv=0.02):
        """
        Light-touch calibration to roughly match €/pax and OPEX/ARV% at current state.
        Call once after init and before first update_for_new_year().
        """
        P = max(1.0, self.traffic)
        ARV = max(1.0, self.asset_replacement_value)
        flights = P / max(1, self.pax_per_movement)
        M = flights

        staff = (self.hr_base + self.hr_per_pax * P + self.hr_per_movement * M) * (1 + self.wage_growth)
        maint = self.maint_pct_arv * ARV + self.maint_per_movement * M
        kwh_term = self.kwh_per_pax * P * self.energy_intensity_factor
        kwh_retail = self.non_aero_sqm * self.kwh_per_sqm
        energy = (kwh_term + kwh_retail) * self.price_per_kwh
        sec   = self.sec_base + self.sec_per_pax * P + self.sec_per_movement * M
        it    = self.it_base + self.it_per_pax * P + self.it_pct_arv * ARV
        rev_guess = (self.traffic * self.aeronautical_charge) + \
                    (self.traffic * self.non_aero_spend_per_pax * (self.non_aero_sqm / 5000)) + \
                    (self.cargo_tonnes * self.cargo_charge_per_tonne)
        insurance = self.ins_pct_arv * ARV + self.ins_pct_revenue * max(0.0, rev_guess)
        env   = (self.co2_per_pax_kg * P / 1000.0) * self.carbon_price + self.noise_per_movement * M
        fee   = self.concession_fee_pct * max(0.0, rev_guess)
        handle= self.handling_per_movement * M
        other = self.other_base * (1 + self.inflation_assumption)
        opex_struct = staff + maint + energy + sec + it + insurance + env + fee + handle + other

        curr_eur_per_pax = opex_struct / P
        curr_pct_arv = opex_struct / ARV

        if curr_eur_per_pax > 0:
            s1 = target_opex_per_pax / curr_eur_per_pax
            self.hr_per_pax *= s1
            self.sec_per_pax *= s1
            self.it_per_pax  *= s1
            self.kwh_per_pax *= s1**0.5
            self.other_base  *= s1**0.5

        if curr_pct_arv > 0:
            s2 = target_opex_pct_arv / curr_pct_arv
            self.maint_pct_arv *= s2
            self.it_pct_arv    *= s2
            self.ins_pct_arv   *= s2

        self.hr_per_movement *= 0.5 + 0.5 * (target_opex_per_pax / max(1e-6, curr_eur_per_pax))
        self.maint_per_movement *= 0.5 + 0.5 * (target_opex_per_pax / max(1e-6, curr_eur_per_pax))

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
        
        if self.traffic > 0:
            opex_per_pax = self.opex / self.traffic
            st.write(f"OPEX per Passenger: €{opex_per_pax:,.2f}")
        if self.asset_replacement_value > 0:
            opex_pct_arv = (self.opex / self.asset_replacement_value) * 100
            st.write(f"OPEX as % of Asset Value: {opex_pct_arv:.2f}%")

        
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

# -----------------------------
# Main Streamlit application
# -----------------------------
st.title("Airport Management Simulation 🛫")

st.markdown(
    """
    <style>
      :root {
        --app-font: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Helvetica Neue', Arial, sans-serif;
      }
      /* Use the same font everywhere */
      .stApp, .stApp * {
        font-family: var(--app-font) !important;
      }
      /* Base body text */
      .stApp p, .stApp li, .stApp span, .stApp div {
        font-size: 16px;
        line-height: 1.5;
      }
      /* Headings */
      .stApp h1 { font-size: 28px; line-height: 1.2; }
      .stApp h2 { font-size: 22px; line-height: 1.3; }
      .stApp h3 { font-size: 18px; line-height: 1.4; }
      /* Streamlit alert boxes: info/warning/error use the same font/size */
      .stAlert, .stAlert p, .stAlert div {
        font-size: 16px !important;
        line-height: 1.5 !important;
      }
    </style>
    """, unsafe_allow_html=True
)# --- Fresh Decisions UI each year: delete widget-state keys tied to labels ---
def _reset_decision_inputs_for_new_year():
    cy = st.session_state.get("current_year", 0)
    last = st.session_state.get("_last_decision_reset_year_v2")
    if last != cy:
        labels_to_clear = {
            "Select a project:",
            "Select campaigns to fund (Max €5M every two years):",
            "Enter OPEX change (% over previous year):",
            "Enter Airport Charges change (% over previous year):",
        }
        # Delete these exact widget keys if present
        for k in list(st.session_state.keys()):
            if k in labels_to_clear or (isinstance(k, str) and k.startswith("Enter the loan amount for ")):
                try:
                    del st.session_state[k]
                except Exception:
                    pass
        st.session_state["_last_decision_reset_year_v2"] = cy


# --- Ensure Decisions tab shows fresh defaults each new year ---
def _reset_decision_inputs_for_new_year():
    cy = st.session_state.get("current_year", 0)
    last = st.session_state.get("_last_decision_reset_year", None)
    if last != cy:
        # Reset common per-year decision inputs to initial defaults
        defaults = {
            "selected_project": None,
            "selected_project_display": None,
            "selected_lead_time": None,
            "selected_available_year": None,
            "loan_amount": 0,
            "marketing_campaigns": [],
            "opex_change_pct": 0.0,
            "airport_charges_change_pct": 0.0,
        }
        for k, v in defaults.items():
            st.session_state[k] = v
        st.session_state["_last_decision_reset_year"] = cy


# --- Unified tab layout to avoid mid-page jumps ---
display_year = st.session_state.get("current_year", 0)
if display_year == 0:
    display_year = 1
st.markdown(f"### Year {display_year}")
tab_setup, tab_decisions, tab_results, tab_history, tab_graphs = st.tabs(["Setup", "Decisions", "Results", "History", "Graphs"])

# --- Authentication (streamlit-authenticator) ---

# 0) Sanity: confirm the package exposes Authenticate
if not hasattr(stauth, "Authenticate"):
    st.error(
        "Your installed 'streamlit-authenticator' does not expose Authenticate().\n"
        "Fix with:\n    py -m pip install --upgrade \"streamlit-authenticator==0.4.1\""
    )
    st.stop()

# 1) Load config.yaml from either the script directory or current working dir
config = None
for candidate in [
    pathlib.Path(__file__).with_name("config.yaml"),
    pathlib.Path("config.yaml")
]:
    if candidate.exists():
        with candidate.open("r", encoding="utf-8") as f:
            config = yaml.load(f, Loader=SafeLoader)
        break

if not config:
    st.error("Error: 'config.yaml' file not found next to the app or in the working directory.")
    st.stop()

# 2) Minimal validation + ensure correct types
if "credentials" not in config or "cookie" not in config:
    st.error("config.yaml must have top-level 'credentials' and 'cookie' sections.")
    st.stop()

for k in ("name", "key", "expiry_days"):
    if k not in config["cookie"]:
        st.error(f"config.yaml missing cookie setting: '{k}'.")
        st.stop()

try:
    config["cookie"]["expiry_days"] = int(config["cookie"]["expiry_days"])
except Exception:
    st.error("Error: 'cookie.expiry_days' must be an integer (e.g., 30).")
    st.stop()

# 3) Build the authenticator (positional args = version-proof)
authenticator = stauth.Authenticate(
    config["credentials"],
    config["cookie"]["name"],
    config["cookie"]["key"],
    config["cookie"]["expiry_days"]
)

# 4) Login – prefer NEW API first, fallback to OLD tuple API
name = username = authentication_status = None

try:
    # NEW API (>= 0.4.x): pass only location; results stored in st.session_state
    authenticator.login(location='main')  # use 'sidebar' if you want it in the sidebar
    name = st.session_state.get("name")
    authentication_status = st.session_state.get("authentication_status")
    username = st.session_state.get("username")

except TypeError:
    # OLD API (< 0.4): returns (name, authentication_status, username)
    name, authentication_status, username = authenticator.login('Login', 'main')


# 5) Handle login states
if authentication_status:
    authenticator.logout("Logout", "main")
    # You can show a brief welcome or proceed with the app:
    # st.success(f"Welcome {name} 👋")
else:
    if authentication_status is False:
        st.error("Username/password is incorrect")
    else:
        st.warning("Please enter your username and password")
    st.stop()

# -----------------------------
# From here down: your app runs for authenticated users
# -----------------------------

if 'airport' not in st.session_state:
    st.session_state.airport = Airport(
        initial_traffic=10_000_000,
        initial_equity=500_000_000,
        initial_assets=500_000_000,
        initial_opex_ratio=0.1,
        initial_asset_value=1_000_000_000,
        initial_cargo_tonnes=500_000
    )

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
    with tab_setup:
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
        st.subheader("Global Scenario")
        scenario = st.selectbox(
            "Choose an external environment scenario:",
            ["Baseline", "High Energy Crisis", "High Inflation", "Carbon Tax Surge"]
        )
        st.session_state["scenario"] = scenario

        st.subheader("Extraordinary Shocks")
        shock_prob = st.slider("Shock Probability (% per year):", 0, 50, 3)
        st.session_state.airport.shock_prob = shock_prob / 100.0

        st.subheader("OPEX Calculation Mode")
        st.session_state.airport.opex_mode = st.radio(
            "Choose OPEX calculation method:",
            ["ratio", "structured"],
            format_func=lambda x: "Legacy Ratio-Based" if x == "ratio" else "Structured Costs",
            key="opex_mode_radio"
        )

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
    with tab_results:
        st.balloons()
        st.header("Simulation Complete!")
        st.write("You have reached the end of the 10-year simulation. Rerun the app to start over.")
        scroll_to_top()
else:
    if st.session_state.simulate_clicked:
        with tab_results:

            # Display Input Summary
            st.header(f"Results for Year {st.session_state.current_year}")
            st.subheader("Input Summary")

            st.write(f"**CAPEX Project:** {st.session_state.get('selected_project_display', 'None') if st.session_state.get('selected_project_display', 'None') != 'Expand Runway' else 'Additional Runway'}")
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

            # Mid-page advance button (between Cash Balance and Simulation Overview)
            if st.button("Advance to Next Year", key="advance_mid_results"):
                advance_year()

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
            st.markdown("<br><br><br>", unsafe_allow_html=True)
            if st.button("Advance to Next Year"):
                advance_year()
            scroll_to_top()
    with tab_decisions:
        _reset_decision_inputs_for_new_year()
        _reset_decision_inputs_for_new_year()
        st.session_state.airport.year = st.session_state.current_year
        st.header(f"Decisions for Year {st.session_state.current_year}")
        gdp_growth = st.session_state.gdp_data.get(st.session_state.current_year, 2.0)
        st.write(f"Predicted GDP Growth for the year: **{gdp_growth}%**")

        st.subheader("CAPEX Projects")
        project_options = {
            'None': 0, 'New Terminal': 1, 'Additional Runway': 2, 'Cargo Hangar': 3, 'Non-Aero Retail Expansion': 4
        }
        selected_project = st.selectbox("Select a project:", list(project_options.keys()), index=0, key=f"dec_project_{st.session_state.current_year}")

        lead_time = 0
        project_availability_year = 0
        if selected_project in ['New Terminal', 'Additional Runway']:
            lead_time = 3
            project_availability_year = st.session_state.current_year + lead_time
        elif selected_project in ['Cargo Hangar', 'Non-Aero Retail Expansion']:
            lead_time = 1
            project_availability_year = st.session_state.current_year + lead_time

        if selected_project != 'None':
            st.write(f"**Lead Time:** {lead_time} years")
            st.write(f"**Project Available:** Year {project_availability_year}")

        loan_amount = 0
        if selected_project in ['New Terminal', 'Additional Runway', 'Non-Aero Retail Expansion']:
            cost_options = {'New Terminal': 150_000_000, 'Additional Runway': 250_000_000, 'Non-Aero Retail Expansion': 50_000_000}
            cost = cost_options.get(selected_project, 0)
            # Compute gearing-based max loan and show it
            equity = st.session_state.airport.equity
            debt = st.session_state.airport.debt
            room = 0.6 * equity - debt
            room = room if room > 0 else 0.0
            max_loan_allowed = min(float(cost), float(room))
            st.caption(f"Max loan allowed by gearing: ${max_loan_allowed:,.0f}")
            loan_amount = st.number_input(
                f"Enter the loan amount for Year {st.session_state.current_year} for project {selected_project} (max {cost:,.0f}):",
                value=0.0,
                max_value=float(max_loan_allowed),
                step=10000.0,
                key=f"dec_loan_{st.session_state.current_year}",
            )
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
        selected_campaigns = st.multiselect("Select campaigns to fund (Max €5M every two years):", list(marketing_options.keys()), default=[], key=f"dec_mkt_{st.session_state.current_year}")

        st.subheader("Annual Operational Changes")
        opex_change = st.number_input("Enter OPEX change (% over previous year):", value=0.0, key=f"dec_opex_{st.session_state.current_year}")
        aero_charge_change = st.number_input("Enter Airport Charges change (% over previous year):", value=0.0, key=f"dec_charges_{st.session_state.current_year}")

        if st.button("Simulate Year"):
            # --- Validate funding before proceeding ---
            _equity = st.session_state.airport.equity
            _debt = st.session_state.airport.debt
            _cash = st.session_state.airport.cash_balance
            # Mirror cost based on selected project
            if selected_project == 'New Terminal':
                _cost_chk = 150_000_000
            elif selected_project == 'Additional Runway':
                _cost_chk = 250_000_000
            elif selected_project == 'Non-Aero Retail Expansion':
                _cost_chk = 50_000_000
            else:
                _cost_chk = 0

            _room = max(0.0, 0.6 * _equity - _debt)

            _invalid = False
            if selected_project != 'None':
                # Loan feasibility by gearing
                if loan_amount > min(_cost_chk, _room):
                    st.error(f"Loan denied: requested ${loan_amount:,.0f} exceeds max allowed by gearing (${_room:,.0f}). Project cannot be funded; choose a lower-cost project or reduce loan.")
                    _invalid = True

                # Funding gap check (cash < cost - loan)
                _equity_needed = _cost_chk - loan_amount
                if _cash < _equity_needed:
                    _gap = _equity_needed - _cash
                    st.warning(
    f"Funding gap: need {int(_gap):,} more equity. "
    f"Increase the loan (up to {int(min(_cost_chk, _room)): ,}) or pick a cheaper project.",
    icon="⚠️"
)
                    _invalid = True

            if _invalid:
                st.stop()


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
                elif project_name == 'Additional Runway':
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

            # Update for new year
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
            st.session_state['_flash_go_top_msg'] = True
            st.rerun()
        scroll_to_top()

        # Show a hint after simulation click
        if st.session_state.get('_flash_go_top_msg'):
            st.info('Go to the top of the page to check results for this year')
            st.session_state['_flash_go_top_msg'] = False



with tab_history:
    st.subheader("Strategic Decisions (Global Settings)")
    st.write(f"Airport Strategy: {st.session_state.airport.strategy}")
    st.write(f"OPEX Calculation Mode: {st.session_state.airport.opex_mode}")
    st.write(f"Global Scenario: {st.session_state.get('scenario', 'Baseline')}")
    st.write(f"Shock Probability: {st.session_state.airport.shock_prob*100:.1f}%")

    st.subheader("Decision History")
    history_data = st.session_state.get("history", [])
    if history_data:
        for entry in history_data:
            y = entry.get("Year", "?")
            st.markdown(f"### Year {y}")
            lines = []
            # CAPEX project and timing
            capex = entry.get("CAPEX Project")
            if capex is not None:
                lines.append(f"- **CAPEX Project:** {capex if capex != 'Expand Runway' else 'Additional Runway'}")
            lt = entry.get("Lead Time")
            if lt is not None:
                lines.append(f"- **Lead Time:** {lt}")
            avail = entry.get("Available Year")
            if avail is None:
                avail = entry.get("Project Available in Year")
            if avail is not None:
                lines.append(f"- **Project Available in Year:** {avail}")
            # Loan amount
            loan = entry.get("Loan Amount")
            if loan is not None:
                try:
                    loan_val = float(loan)
                    lines.append(f"- **Loan Amount:** ${loan_val:,.2f}")
                except Exception:
                    lines.append(f"- **Loan Amount:** {loan}")
            # Marketing campaigns
            mkt = entry.get("Marketing Campaigns")
            if mkt:
                if isinstance(mkt, (list, tuple)):
                    mkt_text = ", ".join(map(str, mkt))
                else:
                    mkt_text = str(mkt)
                lines.append(f"- **Marketing Campaigns:** {mkt_text}")
            # OPEX / Charges
            opex = entry.get("OPEX Change (%)")
            if opex is not None:
                lines.append(f"- **OPEX Change (%):** {opex}%")
            charges = entry.get("Airport Charges Change (%)")
            if charges is not None:
                lines.append(f"- **Airport Charges Change (%):** {charges}%")
            if not lines:
                lines.append("_No decisions recorded for this year._")
            st.markdown("\n".join(lines))
            st.markdown("---")
    else:
        st.info("No history available yet. Simulate a year to see decision history.")



with tab_graphs:
    st.header(f"Simulation Graphs (Years 1 to {st.session_state.current_year})")
    history_df = pd.DataFrame(st.session_state.history)
    if history_df.empty:
        st.info("No graphs yet. Simulate at least one year to see charts.")
    else:
        st.subheader("Simulation Graphs")

        # 1. Traffic Development

        st.subheader("Capacity & Traffic")

        st.line_chart(history_df, x='Year', y=['Traffic', 'Capacity'])
        # 2. Capacity Utilisation - Line Chart
        st.subheader("Capacity Utilisation")
        utilization_df = history_df[['Year', 'Terminal Utilization', 'Runway Utilization']].melt('Year', var_name='Metric', value_name='Utilization (%)')
        util_chart = alt.Chart(utilization_df).mark_bar().encode(
            x=alt.X('Year:O', axis=alt.Axis(title='Year')),
            y=alt.Y('Utilization (%):Q', axis=alt.Axis(title='Utilization (%)')),
            color=alt.Color('Metric:N', legend=alt.Legend(title='Metric')),
            xOffset='Metric:N',
            tooltip=['Year', 'Metric', alt.Tooltip('Utilization (%):Q', format='.2f')]
        ).properties(title="Capacity Utilisation (Grouped Bars)")
        st.altair_chart(util_chart, use_container_width=True)



        # 3. Profit and Cash Flow
        st.subheader("Profit and Cash Flow")
        financial_df = history_df[['Year', 'Profit', 'Cash Balance (End of Year)']].set_index('Year')
        st.line_chart(financial_df)

        # 4. Traffic Impact Analysis - Line Chart
        st.subheader("Traffic Impact Analysis")
        impact_df = history_df[[
            'Year',
            'Quality Impact on Traffic (%)',
            'Aero Charges Impact on Traffic (%)',
            'Cost Impact on Traffic (%)'
        ]].melt("Year", var_name="Metric", value_name="Impact (%)")
        impact_chart = alt.Chart(impact_df).mark_bar().encode(
            x=alt.X('Year:O', axis=alt.Axis(title='Year')),
            y=alt.Y('Impact (%):Q', axis=alt.Axis(title='Impact (%)')),
            color=alt.Color('Metric:N', legend=alt.Legend(title='Impact Driver')),
            xOffset='Metric:N',
            tooltip=['Year', 'Metric', alt.Tooltip('Impact (%):Q', format='.2f')]
        ).properties(title="Traffic Impact Analysis (Grouped Bars)")
        st.altair_chart(impact_chart, use_container_width=True)
