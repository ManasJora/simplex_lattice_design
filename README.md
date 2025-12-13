# Overview
    The `simplex_lattice_design_v70_5` function is a comprehensive formulation tool designed to generate Simplex-Lattice mixture designs. 
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
    -   **Excel Export (.xlsx):** File containing two sheets: 'Datapoints' (the design) and 'Parameters' (input settings).

    # Change Log
    -   **v70.5 (Dec/13/2025):**
        -   **Environment:** Added `google.colab.output.enable_custom_widget_manager()` inside the function to automatically enable third-party widgets in Colab without manual user intervention.
    -   **v70.4 (Dec/13/2025):**
        -   **UI:** Adjusted label widths for "Max Active" and "Density" fields to remove truncation ellipsis (...).
    -   **v70.3 (Dec/13/2025):**
        -   **Environment:** Added automatic detection and enabling of Google Colab custom widget manager logic.
    -   **v70.2 (Dec/13/2025):**
        -   **Architecture:** Moved all library imports inside the function to ensure self-containment.
        -   **Dependencies:** Added explicit `openpyxl` import for Excel export stability.
        -   **UI:** Adjusted numeric input widths to approx 8 chars (~80px).
    -   **v70.1 (Dec/13/2025):**
        -   **Export:** Changed from CSV to Excel (.xlsx) to support multiple sheets ('Datapoints' and 'Parameters').
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
    simplex_lattice_design_v70_5()
    ```

    # Credits
    -   **Author:** Manazael Zuliani Jora
    -   **Date:** Dec/13/2025
    """
