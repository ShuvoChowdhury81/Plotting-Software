# Plotting Software

A desktop scientific plotting application built with **PyQt6** and **Matplotlib**, inspired by Tecplot. Create, customize, and export publication-quality 2D plots with an intuitive GUI.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![PyQt6](https://img.shields.io/badge/GUI-PyQt6-green)
![Matplotlib](https://img.shields.io/badge/Plots-Matplotlib-orange)

---

## Features

- **Data Import** — Load `.dat` and delimited text files; append and manage multiple datasets.
- **Multiple Mapping Styles** — XY Line, 2D Coordinates, Histogram, and more.
- **Curve Fitting** — Linear, Polynomial, Exponential, Power, and Cubic Spline fits with R² display.
- **Axis Customization** — Titles, fonts, colors, log scale, reverse, grid lines, and tick control.
- **Legend Editor** — Position, font, box style, and per-mapping visibility.
- **Frame Size & Position** — Control paper size, orientation, and plot dimensions.
- **Mapping Style Dialog** — Line styles, colors, widths, symbols, and error bars per mapping.
- **Plot Packages** — Save and reload entire plot sessions (data + configuration) as `.pkg` files.
- **Export** — Save plots as PNG, SVG, PDF, and other image formats.
- **Zoom & Pan** — Interactive scroll-zoom and click-drag panning on the canvas.

## Project Structure

```
Ploting Software/
├── main.py                  # Application entry point
├── ui/
│   ├── main_window.py       # Main GUI window (CleanTecplotGUI)
│   ├── widgets/
│   │   └── switch.py        # Custom toggle switch widget
│   └── dialogs/
│       ├── mapping_style.py # Mapping Style dialog
│       ├── legend_style.py  # Legend editor dialog
│       ├── axis_details.py  # Axis Details dialog
│       ├── frame_size.py    # Frame Size & Position dialog
│       ├── append_data.py   # Append Data dialog
│       └── data_manager.py  # Data Set Manager dialog
├── utils/                   # Utility modules
├── requirements.txt
└── README.md
```

## Getting Started

### Prerequisites

- Python 3.10 or higher

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/<your-username>/plotting-software.git
   cd plotting-software
   ```

2. **Create a virtual environment** (recommended)
   ```bash
   python -m venv venv
   venv\Scripts\activate        # Windows
   # source venv/bin/activate   # macOS / Linux
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

### Run

```bash
python main.py
```

## Usage

1. Click **📂 Load Data** to import a `.dat` file.
2. Use the **Mapping Style** dialog to configure line colors, styles, and curve fits.
3. Adjust axes via **📏 Axis Details** and frame size via **🖼️ Frame Size**.
4. Save your work as a Plot Package (`.pkg`) with **Ctrl+S**, or export as an image with **💾 Save Plot**.

## License

This project is provided as-is for personal and academic use.
