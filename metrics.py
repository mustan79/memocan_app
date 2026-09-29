from datetime import date, timedelta

import wx

from i18n import tr


def duration(seconds, language):
    minutes = int(seconds) // 60
    return tr(language, "duration", hours=minutes // 60, minutes=minutes % 60)


class MetricsDialog(wx.Dialog):
    def __init__(self, parent, store, language, flush):
        super().__init__(parent, title=tr(language, "metrics"), size=(780, 620),
                         style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        self.store, self.language, self.flush = store, language, flush
        self.today = date.today()
        self.weeks = store.available_weeks(self.today)
        layout = wx.BoxSizer(wx.VERTICAL)
        layout.Add(wx.StaticText(self, label=tr(language, "week_select")), 0, wx.ALL, 10)
        self.week = wx.Choice(self, choices=[self.week_label(d) for d in self.weeks], name=tr(language, "week_select"))
        self.week.SetSelection(0)
        layout.Add(self.week, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 10)
        self.summary = wx.TextCtrl(self, style=wx.TE_MULTILINE | wx.TE_READONLY, size=(-1, 110), name=tr(language, "week_summary"))
        layout.Add(self.summary, 0, wx.ALL | wx.EXPAND, 10)
        self.day = wx.Choice(self, name=tr(language, "day_select"))
        layout.Add(wx.StaticText(self, label=tr(language, "day_select")), 0, wx.LEFT | wx.RIGHT, 10)
        layout.Add(self.day, 0, wx.EXPAND | wx.ALL, 10)
        self.daily = wx.TextCtrl(self, style=wx.TE_MULTILINE | wx.TE_READONLY, size=(-1, 100), name=tr(language, "day_summary"))
        layout.Add(self.daily, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 10)
        note = wx.StaticText(self, label=tr(language, "metrics_note"))
        note.Wrap(720)
        layout.Add(note, 1, wx.ALL | wx.EXPAND, 10)
        refresh = wx.Button(self, label=tr(language, "refresh"))
        refresh.Bind(wx.EVT_BUTTON, lambda _: self.refresh())
        layout.Add(refresh, 0, wx.ALL | wx.ALIGN_RIGHT, 10)
        layout.Add(self.CreateButtonSizer(wx.CLOSE), 0, wx.ALL | wx.ALIGN_RIGHT, 10)
        self.SetSizer(layout)
        self.Bind(wx.EVT_BUTTON, lambda _: self.EndModal(wx.ID_CLOSE), id=wx.ID_CLOSE)
        self.week.Bind(wx.EVT_CHOICE, lambda _: self.load_week())
        self.day.Bind(wx.EVT_CHOICE, lambda _: self.load_day())
        self.load_week()
        self.week.SetFocus()

    def week_label(self, monday):
        label = f"{monday:%d.%m.%Y} – {monday+timedelta(days=6):%d.%m.%Y}"
        if monday <= self.today <= monday+timedelta(days=6):
            label += " — " + tr(self.language, "current_week")
        return label

    def text(self, title, values):
        return (f"{title}\n" + tr(self.language, "metrics_values",
                active=duration(values['active_seconds'], self.language),
                pc=duration(values['pc_seconds'], self.language), water=values['water_count']))

    def load_week(self, selected_day=None):
        self.flush()
        monday = self.weeks[self.week.GetSelection()]
        total, self.days = self.store.week_metrics(monday)
        self.summary.SetValue(self.text(tr(self.language, "week_summary"), total))
        self.day.SetItems([f"{d:%d.%m.%Y}" + (" — " + tr(self.language, "today") if d == self.today else "") for d, _ in self.days])
        dates = [d for d, _ in self.days]
        target = selected_day or self.today
        self.day.SetSelection(dates.index(target) if target in dates else 0)
        self.load_day()

    def load_day(self):
        index = self.day.GetSelection()
        if index >= 0:
            day, values = self.days[index]
            self.daily.SetValue(self.text(f"{day:%d.%m.%Y}", values))

    def refresh(self):
        selected_week = self.weeks[self.week.GetSelection()]
        selected_day = self.days[self.day.GetSelection()][0]
        self.flush()
        self.today = date.today()
        self.weeks = self.store.available_weeks(self.today)
        self.week.SetItems([self.week_label(d) for d in self.weeks])
        self.week.SetSelection(self.weeks.index(selected_week) if selected_week in self.weeks else 0)
        self.load_week(selected_day)
