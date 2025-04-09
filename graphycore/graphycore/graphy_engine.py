import os
import pandas as pd
import seaborn as sns

# ✅ Use non-GUI backend for Matplotlib (important for servers)
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.cm as cm

import plotly.express as px
import plotly.graph_objects as go
import altair as alt


def read_file(file_path):
    ext = file_path.split('.')[-1].lower()
    if ext in ['xlsx', 'xls']:
        xls = pd.ExcelFile(file_path)
        sheets = xls.sheet_names
        dfs = {sheet: xls.parse(sheet) for sheet in sheets}
        return dfs
    elif ext == 'csv':
        return {'Sheet1': pd.read_csv(file_path)}
    else:
        raise ValueError("Unsupported file type. Use CSV or Excel.")


def clean_dataframe(df):
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    for col in df.columns:
        if df[col].dtype == 'object':
            try:
                df[col] = pd.to_datetime(df[col])
            except Exception:
                continue
    return df


def detect_and_plot(df, output_folder='charts', sheet_name="Sheet"):
    os.makedirs(output_folder, exist_ok=True)

    if len(df) > 100_000:
        df = df.sample(100_000, random_state=42)

    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    categorical_cols = df.select_dtypes(include=['object', 'category', 'bool']).columns.tolist()
    datetime_cols = df.select_dtypes(include=['datetime64[ns]']).columns.tolist()

    # === NUMERIC VISUALS ===
    for col in numeric_cols:
        # Histogram
        plt.figure(figsize=(6, 4))
        sns.histplot(df[col].dropna(), kde=True, color='orange')
        plt.title(f'Distribution of {col}')
        plt.tight_layout()
        plt.savefig(f'{output_folder}/{sheet_name}_hist_{col}.png')
        plt.close()

        # Boxplot
        plt.figure(figsize=(6, 4))
        sns.boxplot(x=df[col], color='skyblue')
        plt.title(f'Boxplot of {col}')
        plt.tight_layout()
        plt.savefig(f'{output_folder}/{sheet_name}_box_{col}.png')
        plt.close()

        # Violin Plot
        plt.figure(figsize=(6, 4))
        sns.violinplot(x=df[col], color='violet')
        plt.title(f'Violin Plot of {col}')
        plt.tight_layout()
        plt.savefig(f'{output_folder}/{sheet_name}_violin_{col}.png')
        plt.close()

        # Altair
        alt.Chart(df).mark_bar().encode(
            alt.X(col, bin=True),
            y='count()'
        ).properties(
            title=f"Altair Histogram of {col}",
            width=500,
            height=300
        ).save(f'{output_folder}/{sheet_name}_altair_hist_{col}.html')

    # === CATEGORICAL VISUALS ===
    for col in categorical_cols:
        value_counts = df[col].value_counts().nlargest(10)

        # Seaborn Bar
        plt.figure(figsize=(6, 4))
        sns.barplot(x=value_counts.index, y=value_counts.values, palette='Set2')
        plt.xticks(rotation=45)
        plt.title(f'Top categories of {col}')
        plt.tight_layout()
        plt.savefig(f'{output_folder}/{sheet_name}_count_{col}.png')
        plt.close()

        # Pie chart
        plt.figure(figsize=(6, 6))
        value_counts.plot.pie(autopct='%1.1f%%')
        plt.title(f'Pie Chart: {col}')
        plt.ylabel("")
        plt.tight_layout()
        plt.savefig(f'{output_folder}/{sheet_name}_pie_{col}.png')
        plt.close()

        # Plotly Pie
        fig = px.pie(values=value_counts.values, names=value_counts.index, title=f"Plotly Pie: {col}")
        fig.write_html(f"{output_folder}/{sheet_name}_plotly_pie_{col}.html")

    # === TIME SERIES ===
    for time_col in datetime_cols:
        for num_col in numeric_cols:
            plt.figure(figsize=(6, 4))
            sns.lineplot(x=df[time_col], y=df[num_col])
            plt.xticks(rotation=45)
            plt.title(f'{num_col} over Time ({time_col})')
            plt.tight_layout()
            plt.savefig(f'{output_folder}/{sheet_name}_time_{time_col}_{num_col}.png')
            plt.close()

            # Plotly Line
            fig = px.line(df, x=time_col, y=num_col, title=f'{num_col} Over Time (Plotly)')
            fig.write_html(f'{output_folder}/{sheet_name}_plotly_time_{time_col}_{num_col}.html')

    # === CATEGORICAL vs NUMERIC ===
    for cat_col in categorical_cols:
        for num_col in numeric_cols:
            plt.figure(figsize=(6, 4))
            sns.barplot(data=df, x=cat_col, y=num_col, estimator='mean', ci=None, palette='muted')
            plt.xticks(rotation=45)
            plt.title(f'Avg {num_col} by {cat_col}')
            plt.tight_layout()
            plt.savefig(f'{output_folder}/{sheet_name}_bar_{cat_col}_{num_col}.png')
            plt.close()

            # Plotly
            grouped = df.groupby(cat_col)[num_col].mean().reset_index()
            fig = px.bar(grouped, x=cat_col, y=num_col, title=f'Avg {num_col} by {cat_col} (Plotly)')
            fig.write_html(f'{output_folder}/{sheet_name}_plotly_bar_{cat_col}_{num_col}.html')

    # === CORRELATION HEATMAP ===
    if len(numeric_cols) >= 2:
        corr = df[numeric_cols].corr()
        plt.figure(figsize=(8, 6))
        sns.heatmap(corr, annot=True, cmap='coolwarm', fmt=".2f")
        plt.title('Correlation Heatmap')
        plt.tight_layout()
        plt.savefig(f'{output_folder}/{sheet_name}_correlation_heatmap.png')
        plt.close()

        fig = go.Figure(data=go.Heatmap(
            z=corr.values,
            x=corr.columns,
            y=corr.columns,
            colorscale='Viridis'
        ))
        fig.update_layout(title='Correlation Heatmap (Plotly)')
        fig.write_html(f'{output_folder}/{sheet_name}_plotly_correlation_heatmap.html')

        # Pairplot
        sns.pairplot(df[numeric_cols[:5]].dropna())
        plt.savefig(f'{output_folder}/{sheet_name}_pairplot.png')
        plt.close()

    # === JOINTPLOT ===
    if len(numeric_cols) >= 2:
        sns.jointplot(x=numeric_cols[0], y=numeric_cols[1], data=df, kind='hex')
        plt.savefig(f'{output_folder}/{sheet_name}_jointplot.png')
        plt.close()

    print(f"✅ Charts for '{sheet_name}' saved in '{output_folder}'")
