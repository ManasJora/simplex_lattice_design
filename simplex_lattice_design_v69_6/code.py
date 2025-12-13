import pandas as pd
import numpy as np
import itertools
import plotly.express as px
import plotly.colors as pcolors
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import ipywidgets as widgets
from datetime import datetime
from IPython.display import display, Markdown, clear_output, HTML
from pandas.io.formats.style import Styler
import math

# ==============================================================================
# SIMPLEX LATTICE DESIGN v69.6
# ==============================================================================

def simplex_lattice_design_v69_6():
    r"""
    # Overview
    The `simplex_lattice_design_v69_6` function is a comprehensive formulation tool designed to generate Simplex-Lattice mixture designs.
    It enables formulation scientists to translate active ingredient targets into practical product masses and volumes,
    handling raw material purity, density, and complex solvent balancing logic.

    # Core Logic and Rules
    1.  **Lattice Generation:**
        -   Constructs a standard simplex lattice coordinate matrix ($z$) based on `Degree (m)` (step size = $1/m$).
    2.  **Concentration Scaling:**
        -   **Target Active (i)** = $Base\_Conc_i \times Max\_Active\_Limit_i$.
    3.  **Product Calculation:**
        -   **Product Mass (i)** = $\frac{Target\_Active_i}{Purity_i} \times Total\_Formula\_Mass$.
        -   **Product Volume (i)** = $\frac{Product\_Mass_i}{Density_i}$.
    4.  **Solvent Logic ('is_solvent'):**
        -   **False (Active):** Active content derived strictly from mass/purity.
        -   **True (Solvent):** Calculated as filler to reach `Total Mass`.
            -   *Total Active of Solvent* = (Added Solvent Mass $\times$ Solvent Purity) + $\sum$ (Other Mass $\times$ (1 - Other Purity)).
    5.  **Validation:**
        -   **Mass Closure:** Sum of products must equal Total Mass ($\pm$ 1%).
        -   **Active Limit:** Sum of active percentages must not exceed 100%.
        -   **Purity Check:** Max Active Limit must be $\le$ Product Purity.

    # Visuals
    -   **Plot Selection:** Users must select exactly 3 ingredients via checkboxes to generate a Ternary Diagram (or 2 for a Binary Plot).
    -   **N=2:** Interactive Binary Scatter plot.
    -   **N=3:** Interactive Ternary Diagram (1000x625px) with adjusted margins. Points are blue with black borders, rendered above the grid.
    -   **Formatting:** Axes labels always show 1 decimal place (e.g., 20.0).

    # Parameters (GUI Inputs)
    -   **Global:** Degree, Total Mass, Replicates.
    -   **Ingredients:** Select (for plot), Name, Purity (%), Max Active (%), Density (g/mL), Is Solvent.

    # Returns
    -   Interactive Widget Interface.
    -   Styled Data Table.
    -   Plotly Figures (Selective).
    -   CSV Export.

    # Change Log
    -   **v69.6 (Dec/12/2025):**
        -   **Format:** Graph axes values forced to 1 decimal place (e.g., '20.0').
    -   **v69.5 (Dec/12/2025):**
        -   Table precision 4 decimals. Graph axes formatting.
    -   **v69.4 (Dec/12/2025):**
        -   New ingredients default to unselected.
    -   **v69.3 (Dec/12/2025):**
        -   Updated annotation coordinates and Hover Templates.

    # Test Example
    ```python
    simplex_lattice_design_v69_6()
    ```

    # Credits
    -   **Author:** Manazael Zuliani Jora
    -   **Date:** Dec/12/2025
    """

    # ==============================================================================
    # 1. CALCULATION LOGIC
    # ==============================================================================
    def calculate_design(component_data, degree_m, total_formula_mass, replicate, randomize):
        solvent_component_name = None
        component_names = list(component_data.keys())

        # Palette
        base_palette = px.colors.qualitative.Plotly + px.colors.qualitative.Bold + px.colors.qualitative.Dark24
        while len(base_palette) < len(component_names): base_palette += base_palette
        colors_hex = [base_palette[i] for i in range(len(component_names))]

        # Validation
        solvent_count = sum(1 for data in component_data.values() if data.get('is_solvent', False))
        if solvent_count > 1: raise ValueError("Error: Multiple ingredients marked as 'Is Solvent'. Only 1 is allowed.")
        for name, data in component_data.items():
            if data.get('is_solvent', False): solvent_component_name = name

        product_purity_map = {}
        max_active_map = {}
        density_map = {}

        for name, values_dict in component_data.items():
            p_act = values_dict.get('product_active_wt_perc')
            m_act = values_dict.get('maximum_active_wt_perc')
            dens = values_dict.get('density', 1.0)
            if m_act > p_act: raise ValueError(f"CRITICAL: {name} - Max Active ({m_act}%) > Purity ({p_act}%).")
            if dens <= 0: raise ValueError(f"Error: {name} density must be > 0.")
            product_purity_map[name] = p_act / 100.0
            max_active_map[name] = m_act / 100.0
            density_map[name] = dens

        valid_rows, removed_rows = [], []
        n_components = len(component_names)

        # Lattice Loop
        for p_tuple in itertools.product(range(degree_m + 1), repeat=n_components):
            if sum(p_tuple) == degree_m:
                z = [x / degree_m for x in p_tuple]
                row_data = {}
                temp_product_masses = {}

                # Base Fractions
                for k, name in enumerate(component_names): row_data[f'{name} (Base)'] = z[k]

                # Mass Calc (Non-Solvent)
                calc_names = [n for n in component_names if n != solvent_component_name]
                sum_partial_mass = 0.0
                for name in calc_names:
                    idx = component_names.index(name)
                    target_active = (z[idx] * max_active_map[name]) * total_formula_mass
                    purity = product_purity_map[name]
                    prod_mass = target_active / purity if purity > 0 else 0
                    temp_product_masses[name] = prod_mass
                    sum_partial_mass += prod_mass

                # Solvent Mass
                extra_solvent_mass = 0.0
                for name in calc_names:
                    extra_solvent_mass += temp_product_masses[name] * (1.0 - product_purity_map[name])

                if solvent_component_name:
                    req_solvent = total_formula_mass - sum_partial_mass
                    temp_product_masses[solvent_component_name] = req_solvent
                    own_active = req_solvent * product_purity_map[solvent_component_name]
                    total_solvent_active = own_active + extra_solvent_mass
                    row_data['Extra Solvent from Ingredients [g]'] = extra_solvent_mass
                    row_data['Total Solvent [g]'] = total_solvent_active

                # Assembly
                final_sum_mass = sum(temp_product_masses.values())
                is_valid, reason = True, ""

                if final_sum_mass > (total_formula_mass * 1.01):
                    reason, is_valid = "Sum(Product) > Total Mass", False
                elif final_sum_mass < (total_formula_mass * 0.99) and not solvent_component_name:
                    is_valid = True

                sum_active_wt, sum_prod_wt = 0.0, 0.0

                for name in component_names:
                    p_mass = temp_product_masses.get(name, 0.0)
                    p_vol = p_mass / density_map[name]
                    p_wt = (p_mass / total_formula_mass) * 100.0 if total_formula_mass > 0 else 0

                    row_data[f'{name} (Product mass) [g]'] = p_mass
                    row_data[f'{name} (Product volume) [mL]'] = p_vol
                    row_data[f'{name} (Product wt) [%]'] = p_wt

                    if name == solvent_component_name: a_mass = total_solvent_active
                    else: a_mass = p_mass * product_purity_map[name]

                    a_wt = (a_mass / total_formula_mass) * 100.0 if total_formula_mass > 0 else 0
                    row_data[f'{name} (Active wt) [%]'] = a_wt

                    sum_active_wt += a_wt
                    sum_prod_wt += p_wt

                row_data['Sum (Product mass) [g]'] = final_sum_mass
                row_data['Sum (Product weight) [%]'] = sum_prod_wt
                row_data['Sum (Active weight) [%]'] = sum_active_wt
                row_data['Reason Removed'] = reason

                if sum_active_wt > 100.01:
                    is_valid, row_data['Reason Removed'] = False, "Sum(Active) > 100%"

                if is_valid: valid_rows.append(row_data)
                else: removed_rows.append(row_data)

        # DataFrame Columns
        col_prod_wt = [f'{n} (Product wt) [%]' for n in component_names]
        col_active_wt = [f'{n} (Active wt) [%]' for n in component_names]
        col_mass = [f'{n} (Product mass) [g]' for n in component_names]
        col_vol = [f'{n} (Product volume) [mL]' for n in component_names]

        base_cols = ['Formula Number'] + col_prod_wt + col_active_wt + col_mass + col_vol
        summ_cols = ['Sum (Product mass) [g]', 'Sum (Product weight) [%]', 'Sum (Active weight) [%]']
        extra_cols = ['Extra Solvent from Ingredients [g]', 'Total Solvent [g]'] if solvent_component_name else []
        final_cols = base_cols + summ_cols + extra_cols

        df_valid = pd.DataFrame(valid_rows)
        if not df_valid.empty:
            if replicate > 1: df_valid = pd.concat([df_valid] * replicate, ignore_index=True)
            if randomize: df_valid = df_valid.sample(frac=1).reset_index(drop=True)
            df_valid.insert(0, 'Formula Number', range(1, len(df_valid) + 1))
            df_valid = df_valid.reindex(columns=final_cols)

        df_removed = pd.DataFrame(removed_rows)
        if not df_removed.empty:
            cols_rem = ['Reason Removed'] + [c for c in final_cols if c != 'Formula Number']
            df_removed = df_removed.reindex(columns=cols_rem)

        return df_valid, df_removed, colors_hex, component_names, final_cols

    # ==============================================================================
    # 2. UI & INTERACTION
    # ==============================================================================

    style_css = """
    <style>
    .interface-container {
        background-color: #F0F0F0;
        border: 2px solid black;
        padding: 20px;
        border-radius: 5px;
    }
    .widget-label { font-weight: bold; font-size: 14px; color: black !important; }
    .header-text { font-size: 20px; font-weight: bold; border-bottom: 2px solid #333; padding-bottom: 5px; margin-bottom: 15px; color: black; }
    .sub-header { font-size: 16px; font-weight: bold; margin-top: 10px; color: black; }

    /* Input Styling */
    .widget-text input, .widget-readout input, .widget-hslider input {
        background-color: #666666 !important;
        color: white !important;
        border: 1px solid #333;
        font-weight: bold;
        font-size: 13px;
        padding: 4px;
    }
    /* Arrows (Spinners) */
    input[type=number]::-webkit-inner-spin-button,
    input[type=number]::-webkit-outer-spin-button {
        -webkit-appearance: inner-spin-button !important;
        opacity: 1 !important;
        background: #dddddd !important;
        filter: invert(1);
        height: 100%;
        display: block;
        cursor: pointer;
        margin-left: 2px;
    }
    .widget-checkbox > label { color: black !important; font-weight: bold; }
    tr:hover { background-color: #ffff99 !important; color: black !important; }
    </style>
    """
    display(HTML(style_css))

    # --- Widgets ---
    w_degree = widgets.BoundedIntText(value=3, min=1, max=15, description='Degree (m):', style={'description_width': 'initial'}, layout=widgets.Layout(width='180px'))
    w_mass = widgets.FloatText(value=100.0, description='Total Mass (g):', style={'description_width': 'initial'}, layout=widgets.Layout(width='180px'))
    w_reps = widgets.BoundedIntText(value=1, min=1, max=10, description='Replicates:', style={'description_width': 'initial'}, layout=widgets.Layout(width='180px'))

    w_rand = widgets.Checkbox(value=False, description='Randomize')
    w_csv = widgets.Checkbox(value=False, description='Export CSV')
    w_plot = widgets.Checkbox(value=True, description='Show Plot')
    w_table = widgets.Checkbox(value=True, description='Show Table')

    rows_container = widgets.VBox([])
    component_rows = []

    def on_solvent_change(change):
        if change['new']:
            for row in component_rows:
                if row['w_solvent'] != change['owner']: row['w_solvent'].value = False

    def add_ingredient_row(b=None, initial_data=None):
        idx = len(component_rows) + 1
        data = initial_data if initial_data else {'name': f'Ingredient {idx}', 'purity': 100.0, 'max': 100.0, 'dens': 1.0, 'solvent': False, 'sel': False}

        w_select = widgets.Checkbox(value=data['sel'], indent=False, layout=widgets.Layout(width='30px'))
        w_name = widgets.Text(value=data['name'], placeholder='Name', description='Name:',
                              layout=widgets.Layout(width='400px'), style={'description_width': '45px'})
        w_purity = widgets.BoundedFloatText(value=data['purity'], min=0.0, max=100.0, step=1.0, description='Purity (%):',
                                            layout=widgets.Layout(width='140px'), style={'description_width': '75px'})
        w_max = widgets.BoundedFloatText(value=data['max'], min=0.0, max=100.0, step=1.0, description='Max Active (%):',
                                         layout=widgets.Layout(width='170px'), style={'description_width': '105px'})
        w_dens = widgets.BoundedFloatText(value=data['dens'], min=0.01, max=20.0, step=0.01, description='Density (g/mL):',
                                          layout=widgets.Layout(width='170px'), style={'description_width': '105px'})
        w_solvent = widgets.Checkbox(value=data['solvent'], description='Is Solvent', indent=False, layout=widgets.Layout(width='100px'))
        w_solvent.observe(on_solvent_change, names='value')

        btn_del = widgets.Button(icon='trash', button_style='danger', layout=widgets.Layout(width='40px', height='30px'))

        row_hbox = widgets.HBox([w_select, w_name, w_purity, w_max, w_dens, w_solvent, btn_del],
                                layout=widgets.Layout(align_items='center', margin='4px 0'))

        def delete_row(btn):
            if row_hbox in rows_container.children:
                new_list = list(rows_container.children)
                new_list.remove(row_hbox)
                rows_container.children = tuple(new_list)
            for i, r in enumerate(component_rows):
                if r['hbox'] is row_hbox: component_rows.pop(i); break

        btn_del.on_click(delete_row)
        component_rows.append({
            'hbox': row_hbox, 'w_select': w_select, 'w_name': w_name,
            'w_purity': w_purity, 'w_max': w_max, 'w_dens': w_dens, 'w_solvent': w_solvent
        })
        rows_container.children += (row_hbox,)

    btn_add = widgets.Button(description='Add ingredient', icon='plus', button_style='info', layout=widgets.Layout(width='150px', margin='0 0 10px 0'))
    btn_add.on_click(add_ingredient_row)

    btn_run = widgets.Button(description='GENERATE DESIGN', button_style='success', icon='cogs', layout=widgets.Layout(width='100%', height='50px', margin='20px 0'))
    out_display = widgets.Output()

    # --- Run Handler ---
    def on_run(b):
        out_display.clear_output()
        comp_data = {}

        if len(component_rows) < 2:
            with out_display: display(HTML("<b style='color:red'>⚠️ Needs at least 2 ingredients.</b>"))
            return

        selected_for_plot = []

        for row in component_rows:
            c_name = row['w_name'].value.strip() or "Unnamed"
            comp_data[c_name] = {
                'product_active_wt_perc': row['w_purity'].value,
                'maximum_active_wt_perc': row['w_max'].value,
                'density': row['w_dens'].value,
                'is_solvent': row['w_solvent'].value
            }
            if row['w_select'].value:
                selected_for_plot.append(c_name)

        results_widgets = []
        results_widgets.append(widgets.HTML("<b style='color:black; font-size:16px;'>--- Running Simplex Lattice Design v69.6 ---</b>"))

        try:
            df_valid, df_removed, colors_hex, component_names, final_cols = calculate_design(
                comp_data, w_degree.value, w_mass.value, w_reps.value, w_rand.value
            )

            # Removed Formulas
            if not df_removed.empty:
                results_widgets.append(widgets.HTML(f"<div class='sub-header' style='color:red'>⚠️ WARNING: {len(df_removed)} Formulas Removed</div>"))
                styler_rem = df_removed.style.format(precision=4)
                styler_rem.set_table_styles([
                    {'selector': 'th', 'props': [('background-color', '#d9534f'), ('color', 'white'), ('font-weight', 'bold'), ('text-align', 'center'), ('border', '1px solid #333')]},
                    {'selector': 'td', 'props': [('text-align', 'center'), ('border', '1px solid #333')]}
                ])
                styler_rem.set_properties(subset=['Reason Removed'], **{'color': 'red', 'font-weight': 'bold'})
                results_widgets.append(widgets.HTML(styler_rem.to_html()))
                results_widgets.append(widgets.HTML("<hr>"))

            # Visualization
            if w_plot.value and not df_valid.empty:
                results_widgets.append(widgets.HTML("<div class='sub-header' style='color:black'>Visualization</div>"))

                n_sel = len(selected_for_plot)
                if n_sel < 2 or n_sel > 3:
                    results_widgets.append(widgets.HTML(f"<b style='color:orange'>⚠️ Plot skipped: Select exactly 2 or 3 ingredients via checkboxes. (Selected: {n_sel})</b>"))
                else:
                    df_plot = df_valid.copy()
                    df_hover = df_valid.copy()
                    for c in df_valid.columns:
                        if pd.api.types.is_float_dtype(df_valid[c]): df_hover[c] = df_hover[c].apply(lambda x: f"{x:.4f}")

                    custom_data = df_hover[final_cols].values

                    def create_hover(idx_list):
                        ht = "<b>Formula %{customdata[0]}</b><br>──────────────<br>"
                        for name in selected_for_plot:
                            c_idx = component_names.index(name)
                            color = colors_hex[c_idx]
                            ht += f"<b style='color:{color}'>{name}</b><br>"
                            ht += f"Mass: %{{customdata[{final_cols.index(f'{name} (Product mass) [g]')}]}} g<br>"
                            ht += f"Vol: %{{customdata[{final_cols.index(f'{name} (Product volume) [mL]')}]}} mL<br>"
                            ht += f"Wt: %{{customdata[{final_cols.index(f'{name} (Product wt) [%]')}]}} %<br><br>"
                        ht += "<b>Totals</b><br>"
                        ht += f"Mass: %{{customdata[{final_cols.index('Sum (Product mass) [g]')}]}} g<br>"
                        ht += "<extra></extra>"
                        return ht

                    def get_axis_style(color):
                        # Force 1 decimal formatting with tickformat='.1f'
                        return dict(title='', tickfont=dict(size=18, family="Arial Black", color='black'),
                                    ticklen=15, tickwidth=3, linewidth=5, linecolor=color,
                                    gridcolor=color, griddash='dash', gridwidth=1, ticks='outside', layer='below traces',
                                    dtick=20, tickformat='.1f')

                    fig = None

                    if n_sel == 3:
                        name_a, name_b, name_c = selected_for_plot
                        mask = pd.Series([True]*len(df_plot))
                        others = set(component_names) - set(selected_for_plot)
                        for o in others: mask &= (df_plot[f'{o} (Product mass) [g]'] <= 0.01)
                        plot_data = df_plot[mask]

                        if not plot_data.empty:
                            fig = px.scatter_ternary(plot_data,
                                                     a=f'{name_a} (Product wt) [%]',
                                                     b=f'{name_c} (Product wt) [%]',
                                                     c=f'{name_b} (Product wt) [%]')

                            idx_a, idx_b, idx_c = [component_names.index(n) for n in selected_for_plot]

                            fig.update_layout(width=1000, height=625,
                                              title=dict(text=f'<b>Simplex-Lattice ({name_a}; {name_b}; {name_c})</b>', x=0.5, y=0.98, font=dict(size=24, color='black')),
                                              margin=dict(l=100, r=100, t=160, b=150),
                                              ternary=dict(sum=100,
                                                           aaxis=get_axis_style(colors_hex[idx_a]),
                                                           baxis={**get_axis_style(colors_hex[idx_c]), 'tickangle': 60},
                                                           caxis={**get_axis_style(colors_hex[idx_b]), 'tickangle': -60},
                                                           bgcolor='#f9f9f9'))

                            fig.add_annotation(x=0.5, y=1.3, text=f"<b>{name_a}</b>", showarrow=False, font=dict(color=colors_hex[idx_a], size=22))
                            fig.add_annotation(x=0.1, y=-0.35, text=f"<b>{name_c}</b>", showarrow=False, font=dict(color=colors_hex[idx_c], size=22))
                            fig.add_annotation(x=0.9, y=-0.35, text=f"<b>{name_b}</b>", showarrow=False, font=dict(color=colors_hex[idx_b], size=22))

                            sub_custom = df_hover.loc[plot_data.index, final_cols].values
                            fig.update_traces(
                                customdata=sub_custom,
                                hovertemplate=create_hover(None),
                                marker=dict(size=18, color='#1f77b4', line=dict(width=1, color='black')),
                                cliponaxis=False
                            )
                        else:
                            results_widgets.append(widgets.HTML("<i style='color:red'>No valid points found for this combination (others must be 0).</i>"))

                    elif n_sel == 2:
                        name_a, name_b = selected_for_plot
                        mask = pd.Series([True]*len(df_plot))
                        others = set(component_names) - set(selected_for_plot)
                        for o in others: mask &= (df_plot[f'{o} (Product mass) [g]'] <= 0.01)
                        plot_data = df_plot[mask]

                        if not plot_data.empty:
                            fig = px.scatter(plot_data, x=f'{name_a} (Product wt) [%]', y=f'{name_b} (Product wt) [%]')
                            fig.update_layout(title=dict(text=f'<b>{name_a} vs {name_b}</b>', font=dict(size=24, color='black')),
                                              xaxis=dict(title=f"<b>{name_a} [%]</b>", tickfont=dict(size=18), gridcolor='#ddd', dtick=20, tickformat='.1f'),
                                              yaxis=dict(title=f"<b>{name_b} [%]</b>", tickfont=dict(size=18), gridcolor='#ddd', dtick=20, tickformat='.1f'))
                            sub_custom = df_hover.loc[plot_data.index, final_cols].values
                            fig.update_traces(
                                customdata=sub_custom,
                                hovertemplate=create_hover(None),
                                marker=dict(size=18, color='#1f77b4', line=dict(width=1, color='black')),
                                cliponaxis=False
                            )
                        else:
                            results_widgets.append(widgets.HTML("<i style='color:red'>No valid points found for this combination.</i>"))

                    if fig: results_widgets.append(go.FigureWidget(fig))
                    results_widgets.append(widgets.HTML("<br>"))

            # 3. Design Table
            if w_table.value and not df_valid.empty:
                results_widgets.append(widgets.HTML("<div class='sub-header' style='color:black'>Design Table (Valid Formulas)</div>"))

                styler = df_valid.style.format(precision=4)

                styler.set_table_styles([
                    {'selector': 'th', 'props': [('background-color', '#2c3e50'), ('color', 'white'), ('font-weight', 'bold'), ('text-align', 'center'), ('border', '1px solid #333')]},
                    {'selector': 'td', 'props': [('text-align', 'center'), ('border', '1px solid #333')]},
                    {'selector': 'tr:nth-child(even)', 'props': [('background-color', '#E0E0E0'), ('color', 'black')]},
                    {'selector': 'tr:nth-child(odd)', 'props': [('background-color', '#D3D3D3'), ('color', 'black')]}
                ])
                for i, name in enumerate(component_names):
                    styler.set_properties(subset=[c for c in df_valid.columns if c.startswith(name)], **{'color': colors_hex[i], 'font-weight': 'bold'})

                results_widgets.append(widgets.HTML(styler.to_html()))

            if not w_plot.value and not w_table.value:
                now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                results_widgets.append(widgets.HTML(f"<i>Points generated at {now_str}, but both Table and Plot are False.</i>"))

            if w_csv.value and not df_valid.empty:
                fname = f'simplex_lattice_design_v69_6_{datetime.now().strftime("%H%M%S")}.csv'
                df_valid.to_csv(fname, index=False)
                print(f"✅ CSV Exported: {fname}")

            # Display all
            with out_display:
                display(widgets.VBox(results_widgets))

        except Exception as e:
            with out_display:
                display(HTML(f"<b style='color:red'>⛔ Error: {str(e)}</b>"))

    btn_run.on_click(on_run)

    ui_content = [
        widgets.HTML("<div class='header-text'>🧪 Simplex Lattice Design v69.6</div>"),
        widgets.HTML("<div class='sub-header'>1. Global Settings</div>"),
        widgets.HBox([w_degree, w_mass, w_reps]),
        widgets.HBox([w_plot, w_table, w_csv, w_rand]),
        widgets.HTML("<hr>"),
        widgets.HTML("<div class='sub-header'>2. Ingredients (Select 2 or 3 for Plot)</div>"),
        btn_add, rows_container, widgets.HTML("<hr>"), btn_run, out_display
    ]
    ui = widgets.VBox(ui_content)
    ui.add_class('interface-container')

    defaults = [
        {'name': 'Ingredient 1', 'purity': 100.0, 'max': 100.0, 'dens': 1.0, 'solvent': False, 'sel': True},
        {'name': 'Ingredient 2', 'purity': 100.0, 'max': 100.0, 'dens': 1.0, 'solvent': False, 'sel': True},
        {'name': 'Ingredient 3', 'purity': 100.0, 'max': 100.0, 'dens': 1.0, 'solvent': False, 'sel': True}
    ]
    for d in defaults: add_ingredient_row(initial_data=d)

    display(ui)

# Execute
simplex_lattice_design_v69_6()
