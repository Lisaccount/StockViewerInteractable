# -*- coding: utf-8 -*-
# @Author  : bedeyoux@gmail.com
# @Time    : 2022/10/21 上午10:57
# @Function:

from bokeh.plotting import figure
from bokeh.models import ColumnDataSource, HoverTool, Slider, RadioButtonGroup
from bokeh.layouts import column
from bokeh.server.server import Server


def add_bar_counter(df):
    """
    Adds a 'bar' count column based on the index which is automatically generating when querying the db.
    Args:
        df:

    Returns:

    """
    df['bar'] = range(len(df))


class Candlestick:
    def __init__(self, visual_data):
        add_bar_counter(visual_data)
        self.original_df = visual_data
        self.df = None
        self.source = ColumnDataSource()

        self.radio_default_active = 2
        self.bars_to_display = 60
        self.bar_width = lambda k: int(k * 0.8 * 1000)
        self.scale_dict = {
            0: 1,
            1: 5,
            2: 15,
            3: 30,
            4: 60,
            5: 240,  # 4H
            6: 1440,  # 1D
            7: 10080,  # 1W
        }

        self.plot = None
        self.slider = None
        self.selector = None
        self.radio_group = None

        self.make_radio_group()
        self.make_slider()
        self.my_radio_handler(self.radio_default_active)

        self.update_source()
        self.make_plot()

    def fetch_data(self, s):
        ohlc_dict = {'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last', 'volume': 'sum'}
        new_data = self.original_df.resample('%sMin' % self.scale_dict[s]).agg(ohlc_dict).copy()
        new_data.close = new_data.close.fillna(method='pad')
        new_data = new_data.fillna(method='bfill', axis=1)
        add_bar_counter(new_data)
        return new_data

    def make_column(self):
        return column(
            self.radio_group,
            self.plot,
            self.slider
        )

    def make_radio_group(self):
        self.radio_group = RadioButtonGroup(labels=["1M", "5M", "15M", "30M", "1H", "4H", "1D", "1W"],
                                            active=self.radio_default_active)
        self.radio_group.on_click(self.my_radio_handler)

    def my_radio_handler(self, new):
        print('Radio button option ' + str(new) + ' selected.')
        self.df = self.fetch_data(new)
        last_entry = self.df.shape[0]

        # reset the slider (also calls the slider handler implicitly)
        s = max(self.bars_to_display, last_entry)
        sv = self.slider.value
        self.slider.value = self.slider.end = s
        # if self.slider.value not change, need reset the slider
        if s == sv:
            self.update_source()

    def make_slider(self):
        self.slider = Slider(start=self.bars_to_display, step=1, title="Bar", width=1000, value=self.bars_to_display)
        self.slider.on_change('value', self.slider_handler)

    def slider_handler(self, attr, old, new):
        """
        Handler function for the slider. Updates the ColumnDataSource to a new range given by the slider's position.
        Args:
            attr:
            old:
            new:

        Returns:

        """
        self.update_source()

    def get_display_range(self, ):
        """Set the range of bars to display, based on slider value and desired zoom level. Return (start, end)
        tuple of indices."""

        end = self.slider.value
        start = max(0, (end - self.bars_to_display))
        return start, end

    def update_source(self):
        """Update the data source to be displayed.

        This is called once when the plot initiates, and then every time the slider moves, or a different instrument is
        selected from the dropdown.
        """
        start, end = self.get_display_range()

        # create new view from dataframe
        df_view = self.df.iloc[start:end]

        # create new source
        new_source = df_view.to_dict(orient='list')

        # add colors to be used for plotting bull and bear candles
        colors = ['#D5E1DD' if cl >= op else '#F2583E' for (cl, op)
                  in zip(df_view.close, df_view.open)]
        new_source['colors'] = colors
        new_source['date'] = df_view.index.to_list()

        try:
            self.plot.renderers[1].glyph.width = self.bar_width((df_view.index[1] - df_view.index[0]).total_seconds())
        except:
            pass
        self.source.data = new_source

    def make_plot(self, ):
        """Draw the plot using the ColumnDataSource"""
        src = self.source
        w = self.bar_width(self.scale_dict[self.radio_default_active] * 60)

        TOOLS = "pan,wheel_zoom,box_zoom,reset,save"
        p = figure(x_axis_type="datetime", tools=TOOLS, width=1000, title="candlestick")

        p.segment('date', 'high', 'date', 'low', source=src, color='black')  # plot the wicks
        p.vbar('date', w, 'close', 'open', source=src, line_color='black', fill_color='colors')  # plot the body

        hover = HoverTool(tooltips=[
            ('bar', '@bar'),
            ('date', '@date{%F %T}'),
            ('open', '@open{0.0000f}'),
            ('high', '@high{0.0000f}'),
            ('low', '@low{0.0000f}'),
            ('close', '@close{0.0000f}')
        ],
            formatters={'@date': 'datetime'}
        )
        p.add_tools(hover)
        self.plot = p


class CandlestickServer:
    def __init__(self, *args, **kwargs):
        self.args, self.kwargs = args, kwargs
        self.server = Server({'/': self.handler}, num_procs=1)
        self.server.start()
        print('Opening Bokeh application on http://localhost:5006/')
        self.server.io_loop.start()

    def handler(self, doc):
        doc.add_root(Candlestick(*self.args, **self.kwargs).make_column())
