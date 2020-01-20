import plotly


def get_daily_traffic_chart(x, y):
    chart = plotly.graph_objs.Scatter(
        x=x, y=y, name='Daily traffic', mode='lines+markers'
    )
    figure = plotly.graph_objs.Figure(data=[chart])
    return figure


def get_traffic_dist_chart(x, y):
    chart = plotly.graph_objs.Bar(x=x, y=y, name='Traffic distribution by POP')
    figure = plotly.graph_objs.Figure(data=[chart])
    return figure


def get_daily_traffic_by_hour_chart(x, y):
    chart = plotly.graph_objs.Scatter(x=x, y=y, name='Daily traffic', mode='lines')
    figure = plotly.graph_objs.Figure(data=[chart])
    return figure