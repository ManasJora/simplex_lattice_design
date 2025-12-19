# Simplex Lattice Design Tool 🧪

**Version:** v73.5  
**Author:** Manazael Zuliani Jora  
**Date:** Dec/18/2025

## 📋 Overview

The **Simplex Lattice Design Tool** is a robust Python function designed for formulation scientists and R&D professionals. It automates the creation of **Simplex-Lattice mixture designs**, bridging the gap between theoretical Design of Experiments (DoE) and practical laboratory execution.

Unlike standard statistical software that often deals only in percentages, this tool translates theoretical lattice fractions into practical **masses and volumes**, handling raw material **purity**, **density**, and complex **solvent/impurity balancing**.

---

## 🧠 Business Rules & Calculation Logic

This tool implements specific formulation logic to ensure physical realism in the generated designs. Below are the governing rules:

### 1. Lattice & Target Definition
* **Grid Generation:** The tool generates a standard simplex lattice matrix ($z$) where the step size is $1/m$ ($m$ = Degree).
* **Target Active Calculation:** The lattice fraction ($z_i$) represents the portion of the *Maximum Active Limit* allowed for that ingredient, not the product mass directly.
    $$\text{Target Active Mass}_i = z_i \times \text{Max Active Limit}_i \times \text{Total Formula Mass}$$

### 2. Product Mass Calculation
To achieve the calculated target active mass, the tool adjusts for the raw material's purity:
$$\text{Product Mass}_i = \frac{\text{Target Active Mass}_i}{\text{Purity}_i}$$
* *Constraint:* If `Max Active Limit` > `Purity`, the generation is aborted (physically impossible).

### 3. Solvent & Impurity Logic (The "Is Solvent" Flag)
The tool handles two distinct formulation scenarios based on whether an ingredient is marked as a **Solvent**:

#### Scenario A: No Solvent (All `is_solvent = False`)
* **Logic:** Pure mixture design based on component ratios.
* **Total Mass:** Acts merely as a reference scaling factor. The sum of product masses may not equal the input "Total Mass" exactly, as no filler is added.
* **Visualization:** The Ternary Plot title displays **"Normalized Product Weight %"**, indicating that the points are relative proportions of the ingredients present.

#### Scenario B: Solvent Present (`is_solvent = True`)
* **Constraint:** Only **one** ingredient can be marked as a solvent.
* **Filler Calculation:** The solvent mass is calculated to close the balance:
    $$\text{Solvent Product Mass} = \text{Total Formula Mass} - \sum (\text{Non-Solvent Product Masses})$$
    * *Validation:* If this results in a negative mass, the formulation is discarded.
* **Impurity Handling (Crucial):** The tool assumes that **impurities** (1 - Purity) from all non-solvent ingredients are chemically compatible with the solvent phase. Therefore, the "Active Content" of the solvent is calculated as:
    $$\text{Total Solvent Active} = (\text{Solvent Mass} \times \text{Solvent Purity}) + \sum_{\text{others}} (\text{Product Mass}_i \times (1 - \text{Purity}_i))$$
* **Column Renaming:** To reflect this logic, output columns change dynamically:
    * `Active wt %` $\rightarrow$ `(Component Active + Solvent as active, wt) [%]`
    * `Active Mass` $\rightarrow$ `(Active Mass + Solvent as active) [g]`
* **Visualization:** The Ternary Plot title displays **"Product Weight %"** (Absolute values).

### 4. Volumetric Calculation
Volume is derived post-mass calculation for lab convenience:
$$\text{Product Volume}_i = \frac{\text{Product Mass}_i}{\text{Density}_i}$$

### 5. Validations & Constraints
Formulations are automatically removed from the final set if:
1.  **Mass Closure:** Sum of products exceeds Total Mass + 1% tolerance.
2.  **Negative Mass:** Calculation requires negative solvent (impossible).
3.  **Active Limit:** Sum of all active percentages exceeds 100%.

---

## ✨ Key Features

* **Interactive UI:** Built with `ipywidgets` for easy parameter input (Jupyter/Colab).
* **Dynamic Visualization:**
    * **Ternary Diagrams:** Auto-generates for 3-component selections with dynamic titles.
    * **Binary Scatter:** Auto-generates for 2-component selections.
* **Excel Export:** Generates `.xlsx` files with two sheets:
    * `Datapoints`: The design table.
    * `Parameters`: A log of inputs (Traceability).

## 🛠️ Dependencies

```bash
pip install pandas numpy plotly ipywidgets openpyxl
