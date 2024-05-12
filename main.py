import pandas as pd
import plotly.express as px
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objects as go
from isoweek import Week

GRAPH_HEIGHT = 700
WEEK_TICK = 604800000

dash_app = dash.Dash(__name__)
app = dash_app.server

df = pd.read_csv("SalesDatasetCorr.csv")

# data cleanup
df['Date'] = pd.to_datetime(df['Date'])
df['Time'] = pd.to_datetime(df['Time'], format='%H:%M').dt.time

min_date = df['Date'].min()
max_date = df['Date'].max()
last_week_number = max_date.isocalendar()[1]
week_numbers = ['Week {}'.format(week) for week in range(1, last_week_number + 1)]
time_periods = {'All Weeks': 0}
time_periods.update({week: week_num for week, week_num in zip(week_numbers, range(1, last_week_number + 1))})

branches = df['Branch'].unique()
branches.sort()
branches = branches.tolist()
branches.insert(0, 'All Branches')

INLINE_STYLE_FILTERS = {'display': 'inline-block', 'width': '24%', 'margin-right': '1%'}
INLINE_STYLE_GRAPHS = {'display': 'inline-block', 'width': '49%', 'margin-right': '1%'}
HEADER_STYLE = {'textAlign': 'center', 'color': '#007BFF', 'padding': '10px', 'fontSize': '50px'}
PADDING_STYLE = {'padding': '15px'}

dash_app.layout = html.Div([
    html.H1("Branch Sales Analysis and Customer Insights", style=HEADER_STYLE),

    html.Div([
        html.Div([
            html.Label('Week'),
            dcc.Dropdown(
                id='time-period',
                options=[{'label': period, 'value': period} for period in time_periods.keys()],
                value='All Weeks',
                clearable=False,
            ),
        ], style=INLINE_STYLE_FILTERS),
        html.Div([
            html.Label('Branch'),
            dcc.Dropdown(
                id='branch',
                options=[{'label': branch, 'value': branch} for branch in branches],
                value='All Branches',
                clearable=False,
            ),
        ], style=INLINE_STYLE_FILTERS),
    ], style=PADDING_STYLE),

    # Sales Trends Over Time
    html.Div([
        html.H2("Sales Trends Over Time"),
        dcc.Graph(id='sales-trends')
    ], style=PADDING_STYLE),

    # Profitability Analysis
    html.Div([
        html.H2("Profitability Analysis"),
        dcc.Graph(id='profitability')
    ], style=PADDING_STYLE),

    # Average Transaction Analysis
    html.Div([
        html.H2("Average Transaction Analysis"),
        dcc.Graph(id='avg-transaction')
    ], style=PADDING_STYLE),

    # Product Performance Analysis
    html.Div([
        html.H2("Product Performance Analysis"),
        dcc.Graph(id='product-performance')
    ], style=PADDING_STYLE),

    html.Div([
        # Customer Segmentation
        html.Div([
            html.H2("Customer Segmentation"),
            dcc.Graph(id='customer-segmentation')
        ], style=INLINE_STYLE_GRAPHS),

        # Impact of Gender on Product Preference
        html.Div([
            html.H2("Impact of Gender on Product Preference"),
            dcc.Graph(id='gender-on-product')
        ], style=INLINE_STYLE_GRAPHS),
    ], style=PADDING_STYLE),

    html.Div([
        # Time of Day Analysis
        html.Div([
            html.H2("Sales by Time of Day"),
            dcc.Graph(id='time-of-day')
        ], style={'display': 'inline-block', 'width': '49%', 'margin-right': '5px'}),

        # Sales by Day of the Week
        html.Div([
            html.H2("Sales by Day of the Week"),
            dcc.Graph(id='sales-by-day')
        ], style={'display': 'inline-block', 'width': '49%'}),
    ], style=PADDING_STYLE),

], style=PADDING_STYLE)


@dash_app.callback(
    Output('sales-trends', 'figure'),
    Output('product-performance', 'figure'),
    Output('customer-segmentation', 'figure'),
    Output('avg-transaction', 'figure'),
    Output('profitability', 'figure'),
    Output('time-of-day', 'figure'),
    Output('sales-by-day', 'figure'),
    Output('gender-on-product', 'figure'),
    [Input('time-period', 'value'),
     Input('branch', 'value')]
)
def update_graphs(time_period, branch):
    data = df.copy()

    start_week = time_periods[time_period]

    if branches.index(branch) > 0:
        data = data[data['Branch'] == branch]

    if start_week > 0:
        start_date = Week(2019, start_week).monday()
        start_date = pd.to_datetime(start_date)
        end_date = start_date + pd.Timedelta(weeks=1)
        data = data[data['Date'].between(start_date, end_date, inclusive='right')]

    #Sales Trends
    sales_by_date = data.groupby('Date')['Total'].sum().reset_index()

    fig1 = go.Figure()

    fig1.add_trace(go.Scatter(
        x=sales_by_date['Date'],
        y=sales_by_date['Total'],
        mode='lines+markers',
        marker=dict(
            size=7,
            color=sales_by_date['Total'],
            colorscale='RdYlBu_r',
            showscale=True,
            colorbar=dict(title='Sales')
        )
    ))

    fig1.update_layout(
        xaxis=dict(
            title='Date',
            showgrid=False,
            dtick=WEEK_TICK,
            tickformat="%d-%m"
        ),
        yaxis=dict(
            title='Total Sales (MMK)',
            showgrid=True
        ),
        height=GRAPH_HEIGHT
    )

    # Product Performance Analysis
    fig2 = px.bar(data, x='Product line', y='Total', height=GRAPH_HEIGHT)
    fig2.update_layout(yaxis=dict(title='Total (MMK)'))

    # Customer Segmentation
    customer_sales = data.groupby('Customer type')['Total'].sum()
    fig3 = px.pie(customer_sales, values='Total', names=customer_sales.index, height=GRAPH_HEIGHT)

    # Average Transaction Analysis
    avg_trans_by_date = data.groupby('Date')['Total'].mean().reset_index()
    fig4 = go.Figure()

    fig4.add_trace(go.Scatter(
        x=avg_trans_by_date['Date'],
        y=avg_trans_by_date['Total'],
        mode='lines+markers',
        marker=dict(
            size=7,
            color=avg_trans_by_date['Total'],
            colorscale='Viridis',
            showscale=True,
            colorbar=dict(title='Average Sales')
        )
    ))

    fig4.update_layout(
        xaxis=dict(
            title='Date',
            showgrid=False,
            dtick=WEEK_TICK,
            tickformat="%d-%m"
        ),
        yaxis=dict(
            title='Average Transaction Value (MMK)',
            showgrid=True
        ),
        height=GRAPH_HEIGHT
    )

    # Profitability Analysis
    data['Profit'] = data['Total'] - data['COGS']
    profit_by_date = data.groupby('Date')['Profit'].sum().reset_index()
    fig5 = go.Figure()
    fig5.add_trace(go.Scatter(
        x=profit_by_date['Date'],
        y=profit_by_date['Profit'],
        mode='lines+markers',
        marker=dict(
            size=7,
            color=profit_by_date['Profit'],
            colorscale='Reds',
            showscale=True,
            colorbar=dict(title='Profit')
        )
    ))

    fig5.update_layout(
        xaxis=dict(
            title='Date',
            showgrid=False,
            dtick=WEEK_TICK,
            tickformat="%d-%m"
        ),
        yaxis=dict(
            title='Total Profit (MMK)',
            showgrid=True
        ),
        height=GRAPH_HEIGHT
    )

    # Time of day Analysis
    data['Hour'] = pd.to_datetime(data['Time'], format='%H:%M:%S').dt.hour
    data['Hour Slot'] = pd.cut(data['Hour'], bins=[0, 6, 12, 18, 24],
                               labels=['00 to 06', '06 to 12', '12 to 18', '18 to 24'], right=False)

    time_sales = data.groupby(['Date', 'Hour Slot'], observed=True)['Total'].sum().reset_index()
    time_sales = time_sales.pivot_table(index='Date', columns='Hour Slot', values='Total', fill_value=0, observed=True)

    fig6 = px.imshow(time_sales, labels={'color': 'Total Sales'}, height=GRAPH_HEIGHT)

    # Sales by Day of the Week
    data['Weekday'] = data['Date'].dt.day_name()
    order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    weekday_sales = data.groupby('Weekday')['Total'].sum().reindex(order).reset_index()
    fig7 = px.line_polar(weekday_sales, r='Total', theta='Weekday', line_close=True, height=GRAPH_HEIGHT)

    # Impact of Gender on Product Preference
    gender_product_sales = data.groupby(['Gender', 'Product line'])['Total'].sum().unstack().reset_index()
    gender_product_sales = gender_product_sales.melt(id_vars='Gender', var_name='Product line', value_name='Total')
    fig8 = px.bar(gender_product_sales, x='Product line', y='Total', color='Gender', barmode='group', height=GRAPH_HEIGHT)
    fig8.update_layout(
        xaxis=dict(tickangle=90, tickfont=dict(size=14)))

    return fig1, fig2, fig3, fig4, fig5, fig6, fig7, fig8


# Run the app
if __name__ == '__main__':
    dash_app.run_server(debug=True)
