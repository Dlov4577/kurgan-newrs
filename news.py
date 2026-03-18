import tkinter as tk
from tkinter import ttk, messagebox
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
import threading
import webbrowser
import json
import os
import re
from PIL import Image, ImageTk, ImageDraw
import io
import math


class KurganMobileApp:
    def __init__(self, root):
        self.root = root
        self.root.title("KURGAN — мобильная версия")
        self.root.geometry("400x700")

        # Цветовая схема
        self.colors = {
            'bg': '#0A0A0F',
            'surface': '#14141C',
            'surface_light': '#1E1E2A',
            'card': '#1C1C26',
            'card_hover': '#2A2A36',
            'primary': '#7C5CFC',
            'primary_light': '#9B7FFF',
            'text': '#FFFFFF',
            'text_secondary': '#9A9AB0',
            'text_light': '#6B6B84',
            'border': '#2A2A36',
            'success': '#50E3C2',
            'error': '#FF6B6B'
        }

        self.root.configure(bg=self.colors['bg'])

        # Убираем стандартные рамки
        self.root.overrideredirect(True)

        # Центрируем окно
        self.center_window()

        # Переменные для перемещения
        self.x = 0
        self.y = 0

        # Анимационные переменные
        self.animation_id = None
        self.detail_panel_height = 0
        self.detail_panel_target = 0
        self.detail_panel_visible = False

        # Источники новостей
        self.sources = {
            "Lenta.ru": {
                "url": "https://lenta.ru/rss",
                "icon": "📰",
                "color": "#FF6B6B",
                "description": "Главные новости России и мира"
            },
            "РИА": {
                "url": "https://ria.ru/export/rss2/index.xml",
                "icon": "🌍",
                "color": "#4ECDC4",
                "description": "Оперативные новости и аналитика"
            },
            "РБК": {
                "url": "https://rssexport.rbc.ru/rbcnews/news/30/full.rss",
                "icon": "💼",
                "color": "#FFD93D",
                "description": "Бизнес, финансы, экономика"
            },
            "Спорт": {
                "url": "https://lenta.ru/rss/sport",
                "icon": "⚽",
                "color": "#6BCB77",
                "description": "Все виды спорта"
            },
            "Техно": {
                "url": "https://lenta.ru/rss/tech",
                "icon": "💻",
                "color": "#9D65FF",
                "description": "Технологии и гаджеты"
            }
        }

        self.current_source = "Lenta.ru"
        self.current_news = []
        self.filtered_news = []
        self.favorites = self.load_favorites()
        self.images_cache = {}
        self.selected_news = None

        # Создаем интерфейс
        self.create_widgets()

        # Загружаем новости
        self.load_news()

    def center_window(self):
        """Центрирование окна"""
        self.root.update_idletasks()
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - 400) // 2
        y = (screen_height - 700) // 2
        self.root.geometry(f'400x700+{x}+{y}')

    def create_widgets(self):
        """Создание интерфейса"""

        # ========== ВЕРХНЯЯ ПАНЕЛЬ ==========
        self.create_header()

        # ========== ИНФО ПАНЕЛЬ ==========
        self.create_info_panel()

        # ========== ПАНЕЛЬ УПРАВЛЕНИЯ ==========
        self.create_control_panel()

        # ========== СПИСОК НОВОСТЕЙ ==========
        self.create_news_list()

        # ========== ДЕТАЛЬНАЯ ПАНЕЛЬ ==========
        self.create_detail_panel()

    def create_header(self):
        """Создание заголовка"""
        header = tk.Frame(self.root, bg=self.colors['surface'], height=60)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        # Кнопка меню
        menu_btn = tk.Button(
            header,
            text="☰",
            command=self.show_menu,
            bg=self.colors['surface'],
            fg=self.colors['text'],
            font=("Segoe UI", 18),
            bd=0,
            cursor="hand2",
            activebackground=self.colors['surface_light']
        )
        menu_btn.pack(side=tk.LEFT, padx=15)

        # Заголовок
        title_label = tk.Label(
            header,
            text="KURGAN",
            font=("Segoe UI", 18, "bold"),
            fg=self.colors['primary'],
            bg=self.colors['surface']
        )
        title_label.pack(side=tk.LEFT, padx=5)

        # Индикатор статуса
        self.status_indicator = tk.Label(
            header,
            text="●",
            font=("Segoe UI", 14),
            fg=self.colors['success'],
            bg=self.colors['surface']
        )
        self.status_indicator.pack(side=tk.LEFT, padx=5)

        # Счетчик новостей
        self.news_counter = tk.Label(
            header,
            text="0",
            font=("Segoe UI", 10),
            fg=self.colors['text_light'],
            bg=self.colors['surface']
        )
        self.news_counter.pack(side=tk.LEFT, padx=5)

        # Кнопка закрытия
        close_btn = tk.Button(
            header,
            text="✕",
            command=self.close_app,
            bg=self.colors['surface'],
            fg=self.colors['text'],
            font=("Segoe UI", 16),
            bd=0,
            cursor="hand2",
            activebackground=self.colors['surface_light']
        )
        close_btn.pack(side=tk.RIGHT, padx=15)

        # Перетаскивание
        header.bind("<Button-1>", self.start_move)
        header.bind("<B1-Motion>", self.on_move)

    def create_info_panel(self):
        """Создание информационной панели"""
        self.info_panel = tk.Frame(self.root, bg=self.colors['surface_light'], height=80)
        self.info_panel.pack(fill=tk.X, pady=5)
        self.info_panel.pack_propagate(False)

        # Иконка источника
        self.source_icon = tk.Label(
            self.info_panel,
            text=self.sources[self.current_source]["icon"],
            font=("Segoe UI", 24),
            fg=self.sources[self.current_source]["color"],
            bg=self.colors['surface_light']
        )
        self.source_icon.place(x=15, y=15)

        # Название источника
        self.source_name = tk.Label(
            self.info_panel,
            text=self.current_source,
            font=("Segoe UI", 14, "bold"),
            fg=self.colors['text'],
            bg=self.colors['surface_light']
        )
        self.source_name.place(x=60, y=15)

        # Описание источника
        self.source_desc = tk.Label(
            self.info_panel,
            text=self.sources[self.current_source]["description"],
            font=("Segoe UI", 9),
            fg=self.colors['text_secondary'],
            bg=self.colors['surface_light']
        )
        self.source_desc.place(x=60, y=40)

    def create_control_panel(self):
        """Создание панели управления"""
        panel = tk.Frame(self.root, bg=self.colors['surface'], height=50)
        panel.pack(fill=tk.X, pady=5)
        panel.pack_propagate(False)

        # Выбор источника
        source_frame = tk.Frame(panel, bg=self.colors['surface'])
        source_frame.pack(side=tk.LEFT, padx=10)

        self.source_var = tk.StringVar(value=self.current_source)
        self.source_combo = ttk.Combobox(
            source_frame,
            textvariable=self.source_var,
            values=list(self.sources.keys()),
            state="readonly",
            width=10,
            font=("Segoe UI", 10)
        )
        self.source_combo.pack(side=tk.LEFT)
        self.source_combo.bind('<<ComboboxSelected>>', lambda e: self.change_source())

        # Кнопки
        btn_frame = tk.Frame(panel, bg=self.colors['surface'])
        btn_frame.pack(side=tk.RIGHT, padx=10)

        self.refresh_btn = tk.Button(
            btn_frame,
            text="↻",
            command=self.load_news,
            bg=self.colors['primary'],
            fg='white',
            font=("Segoe UI", 12),
            bd=0,
            width=3,
            cursor="hand2"
        )
        self.refresh_btn.pack(side=tk.LEFT, padx=2)

        self.fav_btn = tk.Button(
            btn_frame,
            text="❤",
            command=self.show_favorites,
            bg=self.colors['primary'],
            fg='white',
            font=("Segoe UI", 12),
            bd=0,
            width=3,
            cursor="hand2"
        )
        self.fav_btn.pack(side=tk.LEFT, padx=2)

    def create_news_list(self):
        """Создание списка новостей"""
        # Контейнер для списка
        list_container = tk.Frame(self.root, bg=self.colors['bg'])
        list_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Поиск
        search_frame = tk.Frame(list_container, bg=self.colors['surface_light'])
        search_frame.pack(fill=tk.X, pady=(0, 10))

        # Иконка поиска
        tk.Label(
            search_frame,
            text="🔍",
            font=("Segoe UI", 12),
            fg=self.colors['text_light'],
            bg=self.colors['surface_light']
        ).pack(side=tk.LEFT, padx=10, pady=8)

        # Поле поиска
        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(
            search_frame,
            textvariable=self.search_var,
            font=("Segoe UI", 11),
            bg=self.colors['surface_light'],
            fg=self.colors['text'],
            insertbackground=self.colors['primary'],
            bd=0
        )
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, pady=8)
        self.search_entry.insert(0, "Поиск новостей...")

        # Счетчик результатов
        self.result_counter = tk.Label(
            search_frame,
            text="0",
            font=("Segoe UI", 10),
            fg=self.colors['text_light'],
            bg=self.colors['surface_light']
        )
        self.result_counter.pack(side=tk.RIGHT, padx=10)

        # Привязки
        self.search_entry.bind('<FocusIn>', self.on_search_focus)
        self.search_entry.bind('<FocusOut>', self.on_search_blur)
        self.search_var.trace('w', lambda *args: self.filter_news())

        # Canvas для прокрутки
        canvas_container = tk.Frame(list_container, bg=self.colors['bg'])
        canvas_container.pack(fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(
            canvas_container,
            bg=self.colors['bg'],
            highlightthickness=0
        )

        scrollbar = tk.Scrollbar(
            canvas_container,
            orient=tk.VERTICAL,
            command=self.canvas.yview
        )

        # Фрейм для карточек
        self.news_frame = tk.Frame(self.canvas, bg=self.colors['bg'])
        self.news_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.news_frame, anchor="nw", width=360)
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def create_detail_panel(self):
        """Создание выдвижной панели для детальной информации"""
        self.detail_panel = tk.Frame(self.root, bg=self.colors['surface'], height=0)
        self.detail_panel.pack(fill=tk.X, side=tk.BOTTOM)
        self.detail_panel.pack_propagate(False)

    def animate_detail_panel(self, target_height):
        """Плавная анимация панели"""
        if self.animation_id:
            self.root.after_cancel(self.animation_id)

        def animate():
            current = self.detail_panel_height
            if current < target_height:
                new_height = min(current + 20, target_height)
                self.detail_panel.configure(height=new_height)
                self.detail_panel_height = new_height
                self.animation_id = self.root.after(10, animate)
            elif current > target_height:
                new_height = max(current - 20, target_height)
                self.detail_panel.configure(height=new_height)
                self.detail_panel_height = new_height
                self.animation_id = self.root.after(10, animate)
            else:
                self.animation_id = None

        animate()

    def show_detail_panel(self, news):
        """Показ детальной информации"""
        if self.detail_panel_visible and self.selected_news == news:
            self.hide_detail_panel()
            return

        self.selected_news = news
        self.detail_panel_visible = True

        # Очищаем панель
        for widget in self.detail_panel.winfo_children():
            widget.destroy()

        # Контент
        content = tk.Frame(self.detail_panel, bg=self.colors['surface'])
        content.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        # Заголовок с кнопкой закрытия
        header = tk.Frame(content, bg=self.colors['surface'])
        header.pack(fill=tk.X, pady=(0, 10))

        # Информация об источнике
        source_info = tk.Frame(header, bg=self.colors['surface'])
        source_info.pack(side=tk.LEFT)

        tk.Label(
            source_info,
            text=news['source_icon'],
            font=("Segoe UI", 16),
            fg=news['source_color'],
            bg=self.colors['surface']
        ).pack(side=tk.LEFT, padx=(0, 5))

        tk.Label(
            source_info,
            text=news['source'],
            font=("Segoe UI", 12, "bold"),
            fg=news['source_color'],
            bg=self.colors['surface']
        ).pack(side=tk.LEFT)

        # Кнопка закрытия
        tk.Button(
            header,
            text="✕",
            command=self.hide_detail_panel,
            bg=self.colors['surface'],
            fg=self.colors['text'],
            font=("Segoe UI", 12),
            bd=0,
            cursor="hand2"
        ).pack(side=tk.RIGHT)

        # Контейнер с прокруткой
        canvas = tk.Canvas(content, bg=self.colors['surface'], highlightthickness=0, height=250)
        scrollbar = tk.Scrollbar(content, orient=tk.VERTICAL, command=canvas.yview)
        scrollable = tk.Frame(canvas, bg=self.colors['surface'])

        scrollable.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable, anchor="nw", width=320)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Детальная информация
        detail = tk.Frame(scrollable, bg=self.colors['surface'])
        detail.pack(fill=tk.BOTH, expand=True)

        # Заголовок новости
        tk.Label(
            detail,
            text=news['title'],
            font=("Segoe UI", 13, "bold"),
            fg=self.colors['text'],
            bg=self.colors['surface'],
            wraplength=300,
            justify=tk.LEFT
        ).pack(anchor=tk.W, pady=(0, 10))

        # Дата и время
        date_frame = tk.Frame(detail, bg=self.colors['surface'])
        date_frame.pack(anchor=tk.W, pady=(0, 10))

        tk.Label(
            date_frame,
            text="📅",
            font=("Segoe UI", 11),
            fg=self.colors['text_light'],
            bg=self.colors['surface']
        ).pack(side=tk.LEFT, padx=(0, 5))

        tk.Label(
            date_frame,
            text=news['date'] if news.get('date') else "Дата неизвестна",
            font=("Segoe UI", 11),
            fg=self.colors['text_secondary'],
            bg=self.colors['surface']
        ).pack(side=tk.LEFT)

        # Полный текст
        if news.get('full_text'):
            text_label = tk.Label(
                detail,
                text=news['full_text'],
                font=("Segoe UI", 11),
                fg=self.colors['text_secondary'],
                bg=self.colors['surface'],
                wraplength=300,
                justify=tk.LEFT
            )
            text_label.pack(anchor=tk.W, pady=(0, 15))

        # Кнопки действий
        btn_frame = tk.Frame(detail, bg=self.colors['surface'])
        btn_frame.pack(fill=tk.X, pady=(5, 0))

        # Кнопка открыть на сайте
        tk.Button(
            btn_frame,
            text="🌐 Читать на сайте",
            command=lambda: webbrowser.open(news['link']),
            bg=self.colors['primary'],
            fg='white',
            font=("Segoe UI", 11),
            bd=0,
            padx=15,
            pady=8,
            cursor="hand2"
        ).pack(fill=tk.X, pady=(0, 5))

        # Кнопка избранного
        is_fav = self.is_favorite(news['link'])
        fav_btn = tk.Button(
            btn_frame,
            text="❤ В избранном" if is_fav else "🤍 В избранное",
            command=lambda: self.toggle_favorite_from_detail(news),
            bg=self.colors['surface_light'],
            fg=self.colors['primary'] if is_fav else self.colors['text'],
            font=("Segoe UI", 11),
            bd=0,
            padx=15,
            pady=8,
            cursor="hand2"
        )
        fav_btn.pack(fill=tk.X)

        # Запускаем анимацию
        self.animate_detail_panel(450)

    def hide_detail_panel(self):
        """Скрытие детальной панели"""
        self.detail_panel_visible = False
        self.animate_detail_panel(0)
        self.root.after(300, lambda: [widget.destroy() for widget in self.detail_panel.winfo_children()])

    def show_menu(self):
        """Показ меню"""
        menu_window = tk.Toplevel(self.root)
        menu_window.title("Меню")
        menu_window.geometry("280x350")
        menu_window.configure(bg=self.colors['surface'])
        menu_window.overrideredirect(True)

        # Центрируем
        x = self.root.winfo_x() + 30
        y = self.root.winfo_y() + 60
        menu_window.geometry(f"280x350+{x}+{y}")

        # Заголовок
        tk.Label(
            menu_window,
            text="МЕНЮ",
            font=("Segoe UI", 18, "bold"),
            fg=self.colors['primary'],
            bg=self.colors['surface']
        ).pack(pady=20)

        # Информация
        info_frame = tk.Frame(menu_window, bg=self.colors['surface_light'])
        info_frame.pack(fill=tk.X, padx=15, pady=10)

        info_text = f"""
        📊 СТАТИСТИКА
        • Всего новостей: {len(self.current_news)}
        • Показано: {len(self.filtered_news)}
        • В избранном: {len(self.favorites)}
        • Источник: {self.current_source}
        """

        tk.Label(
            info_frame,
            text=info_text,
            font=("Segoe UI", 10),
            fg=self.colors['text'],
            bg=self.colors['surface_light'],
            justify=tk.LEFT
        ).pack(padx=15, pady=15)

        # Пункты меню
        menu_items = [
            ("🏠 Все новости", lambda: [menu_window.destroy(), self.show_all_news()]),
            ("❤️ Избранное", lambda: [menu_window.destroy(), self.show_favorites()]),
            ("📱 О приложении", lambda: [menu_window.destroy(), self.show_about()])
        ]

        for text, command in menu_items:
            btn = tk.Button(
                menu_window,
                text=text,
                command=command,
                bg=self.colors['surface_light'],
                fg=self.colors['text'],
                font=("Segoe UI", 12),
                bd=0,
                padx=20,
                pady=10,
                cursor="hand2"
            )
            btn.pack(fill=tk.X, padx=15, pady=2)

        # Кнопка закрытия меню
        tk.Button(
            menu_window,
            text="✕ Закрыть",
            command=menu_window.destroy,
            bg=self.colors['primary'],
            fg='white',
            font=("Segoe UI", 11),
            bd=0,
            padx=20,
            pady=8,
            cursor="hand2"
        ).pack(pady=15)

    def show_about(self):
        """Показ информации о приложении"""
        about_window = tk.Toplevel(self.root)
        about_window.title("О приложении")
        about_window.geometry("300x200")
        about_window.configure(bg=self.colors['surface'])
        about_window.overrideredirect(True)

        # Центрируем
        x = self.root.winfo_x() + 50
        y = self.root.winfo_y() + 150
        about_window.geometry(f"300x200+{x}+{y}")

        tk.Label(
            about_window,
            text="ℹ️ О ПРИЛОЖЕНИИ",
            font=("Segoe UI", 14, "bold"),
            fg=self.colors['primary'],
            bg=self.colors['surface']
        ).pack(pady=15)

        about_text = """
        KURGAN v2.0
        Мобильный новостной агрегатор

        • 5 источников новостей
        • Картинки к новостям
        • Поиск по новостям
        • Избранное
        • Плавные анимации
        • Переход на сайт

        Разработано специально для
        удобного чтения новостей
        """

        tk.Label(
            about_window,
            text=about_text,
            font=("Segoe UI", 10),
            fg=self.colors['text'],
            bg=self.colors['surface'],
            justify=tk.LEFT
        ).pack(pady=10)

        tk.Button(
            about_window,
            text="Закрыть",
            command=about_window.destroy,
            bg=self.colors['primary'],
            fg='white',
            font=("Segoe UI", 10),
            bd=0,
            padx=20,
            pady=5,
            cursor="hand2"
        ).pack(pady=10)

    def show_all_news(self):
        """Показать все новости"""
        self.filtered_news = self.current_news
        self.display_news()
        self.update_info()

    def on_search_focus(self, event):
        if self.search_entry.get() == "Поиск новостей...":
            self.search_entry.delete(0, tk.END)

    def on_search_blur(self, event):
        if not self.search_entry.get():
            self.search_entry.insert(0, "Поиск новостей...")

    def start_move(self, event):
        self.x = event.x
        self.y = event.y

    def on_move(self, event):
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.root.winfo_x() + deltax
        y = self.root.winfo_y() + deltay
        self.root.geometry(f"+{x}+{y}")

    def close_app(self):
        """Закрытие приложения"""
        if messagebox.askokcancel("Выход", "Закрыть приложение?"):
            self.root.destroy()

    def change_source(self):
        self.current_source = self.source_var.get()
        self.update_info()
        self.hide_detail_panel()
        self.load_news()

    def update_info(self):
        """Обновление информационной панели"""
        self.source_icon.config(
            text=self.sources[self.current_source]["icon"],
            fg=self.sources[self.current_source]["color"]
        )
        self.source_name.config(text=self.current_source)
        self.source_desc.config(text=self.sources[self.current_source]["description"])

    def load_news(self):
        self.status_indicator.config(fg=self.colors['error'])
        self.news_counter.config(text="0")
        self.hide_detail_panel()

        for widget in self.news_frame.winfo_children():
            widget.destroy()

        # Анимированная загрузка
        loading_frame = tk.Frame(self.news_frame, bg=self.colors['bg'])
        loading_frame.pack(expand=True, fill=tk.BOTH, pady=50)

        self.loading_angle = 0
        self.animate_loading(loading_frame)

        thread = threading.Thread(target=self._fetch_news, daemon=True)
        thread.start()

    def animate_loading(self, frame):
        """Анимация загрузки"""
        if not hasattr(self, 'loading_angle'):
            self.loading_angle = 0

        frame.destroy()
        loading_frame = tk.Frame(self.news_frame, bg=self.colors['bg'])
        loading_frame.pack(expand=True, fill=tk.BOTH, pady=50)

        # Создаем вращающийся круг
        canvas = tk.Canvas(loading_frame, width=60, height=60, bg=self.colors['bg'], highlightthickness=0)
        canvas.pack()

        self.loading_angle += 10
        for i in range(8):
            angle = self.loading_angle + i * 45
            rad = math.radians(angle)
            x = 30 + 20 * math.cos(rad)
            y = 30 + 20 * math.sin(rad)

            alpha = 0.3 + 0.7 * (i / 8)
            color = self.interpolate_color(self.colors['primary'], self.colors['text'], alpha)

            canvas.create_oval(x - 4, y - 4, x + 4, y + 4, fill=color, outline='')

        self.loading_anim = self.root.after(50, lambda: self.animate_loading(loading_frame))

    def interpolate_color(self, color1, color2, ratio):
        """Интерполяция цветов"""

        def hex_to_rgb(hex_color):
            hex_color = hex_color.lstrip('#')
            return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))

        def rgb_to_hex(rgb):
            return f'#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}'

        rgb1 = hex_to_rgb(color1)
        rgb2 = hex_to_rgb(color2)

        r = int(rgb1[0] * (1 - ratio) + rgb2[0] * ratio)
        g = int(rgb1[1] * (1 - ratio) + rgb2[1] * ratio)
        b = int(rgb1[2] * (1 - ratio) + rgb2[2] * ratio)

        return rgb_to_hex((r, g, b))

    def stop_loading(self):
        """Остановка анимации загрузки"""
        if hasattr(self, 'loading_anim'):
            self.root.after_cancel(self.loading_anim)

    def _fetch_news(self):
        try:
            url = self.sources[self.current_source]["url"]
            headers = {'User-Agent': 'Mozilla/5.0'}

            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            root = ET.fromstring(response.content)

            news_list = []
            for item in root.findall('.//item')[:20]:
                title = self.get_text(item, 'title')
                link = self.get_text(item, 'link')
                desc = self.get_text(item, 'description')
                date = self.get_text(item, 'pubDate')
                image_url = self.extract_image(item)

                full_text = self.get_full_text(item, desc)

                if desc:
                    desc = re.sub(r'<[^>]+>', '', desc)
                    desc = desc[:100] + '...' if len(desc) > 100 else desc

                date = self.format_date(date)

                if title and link:
                    news_list.append({
                        'title': title,
                        'link': link,
                        'description': desc,
                        'full_text': full_text[:500] + '...' if len(full_text) > 500 else full_text,
                        'date': date,
                        'image_url': image_url,
                        'source': self.current_source,
                        'source_icon': self.sources[self.current_source]["icon"],
                        'source_color': self.sources[self.current_source]["color"]
                    })

            self.current_news = news_list
            self.filtered_news = news_list

            self.root.after(0, self.stop_loading)
            self.root.after(0, self.display_news)
            self.root.after(0, self.update_counters)
            self.root.after(0, lambda: self.status_indicator.config(fg=self.colors['success']))

        except Exception as e:
            self.root.after(0, self.stop_loading)
            self.root.after(0, lambda: self.show_error(str(e)))

    def get_text(self, parent, tag):
        elem = parent.find(tag)
        return elem.text if elem is not None else ""

    def get_full_text(self, item, description):
        for elem in item.findall('.//yandex:full-text', {'yandex': 'http://news.yandex.ru'}):
            if elem.text:
                return re.sub(r'<[^>]+>', '', elem.text)

        if description:
            return re.sub(r'<[^>]+>', '', description)

        return "Полный текст недоступен"

    def extract_image(self, item):
        for media in item.findall('.//enclosure'):
            if media.get('type', '').startswith('image/'):
                return media.get('url')

        desc = item.find('description')
        if desc is not None and desc.text:
            img_match = re.search(r'<img[^>]+src="([^">]+)"', desc.text)
            if img_match:
                return img_match.group(1)

        return None

    def format_date(self, date_str):
        if not date_str:
            return ""

        try:
            dt = datetime.strptime(date_str, '%a, %d %b %Y %H:%M:%S %z')
            now = datetime.now(dt.tzinfo)
            diff = now - dt

            if diff.days == 0:
                if diff.seconds < 60:
                    return "Только что"
                elif diff.seconds < 3600:
                    return f"{diff.seconds // 60} мин назад"
                else:
                    return f"{diff.seconds // 3600} ч назад"
            elif diff.days == 1:
                return "Вчера"
            elif diff.days < 7:
                return f"{diff.days} дн назад"
            else:
                return dt.strftime('%d.%m.%Y')
        except:
            return date_str[:16]

    def display_news(self):
        for widget in self.news_frame.winfo_children():
            widget.destroy()

        if not self.filtered_news:
            self.show_empty_state()
            return

        for news in self.filtered_news:
            self.create_news_card(news)

        self.update_counters()

    def create_news_card(self, news):
        """Создание карточки новости с картинкой и кнопками в правом нижнем углу"""

        # Карточка
        card = tk.Frame(
            self.news_frame,
            bg=self.colors['card'],
            bd=0
        )
        card.pack(fill=tk.X, pady=5)

        # Делаем кликабельной (кроме кнопок)
        def on_card_click(e):
            # Проверяем, что клик не по кнопке
            widget = e.widget
            if not isinstance(widget, tk.Button) and widget != fav_btn and widget != site_btn:
                self.show_detail_panel(news)

        card.bind("<Button-1>", on_card_click)

        # Верхний акцент
        accent = tk.Frame(
            card,
            bg=news['source_color'],
            height=3
        )
        accent.pack(fill=tk.X)
        accent.bind("<Button-1>", on_card_click)

        # ===== КАРТИНКА =====
        if news.get('image_url'):
            # Контейнер для картинки
            image_container = tk.Frame(card, bg=self.colors['card'], height=150)
            image_container.pack(fill=tk.X)
            image_container.pack_propagate(False)
            image_container.bind("<Button-1>", on_card_click)

            # Загружаем картинку в отдельном потоке
            self.load_news_image(image_container, news)
        else:
            # Плейсхолдер если нет картинки
            placeholder = tk.Frame(card, bg=self.colors['surface_light'], height=100)
            placeholder.pack(fill=tk.X)
            placeholder.pack_propagate(False)
            placeholder.bind("<Button-1>", on_card_click)

            tk.Label(
                placeholder,
                text=news['source_icon'],
                font=("Segoe UI", 32),
                fg=self.colors['text_light'],
                bg=self.colors['surface_light']
            ).pack(expand=True)

        # Контент
        content = tk.Frame(card, bg=self.colors['card'])
        content.pack(fill=tk.X, padx=12, pady=12)
        content.bind("<Button-1>", on_card_click)

        # Верхняя строка
        top_row = tk.Frame(content, bg=self.colors['card'])
        top_row.pack(fill=tk.X, pady=(0, 8))
        top_row.bind("<Button-1>", on_card_click)

        # Иконка и источник
        source_frame = tk.Frame(top_row, bg=self.colors['card'])
        source_frame.pack(side=tk.LEFT)
        source_frame.bind("<Button-1>", on_card_click)

        source_icon_label = tk.Label(
            source_frame,
            text=news['source_icon'],
            font=("Segoe UI", 12),
            fg=news['source_color'],
            bg=self.colors['card']
        )
        source_icon_label.pack(side=tk.LEFT, padx=(0, 5))
        source_icon_label.bind("<Button-1>", on_card_click)

        source_name_label = tk.Label(
            source_frame,
            text=news['source'],
            font=("Segoe UI", 9),
            fg=news['source_color'],
            bg=self.colors['card']
        )
        source_name_label.pack(side=tk.LEFT)
        source_name_label.bind("<Button-1>", on_card_click)

        # Дата
        if news.get('date'):
            date_label = tk.Label(
                top_row,
                text=news['date'],
                font=("Segoe UI", 9),
                fg=self.colors['text_light'],
                bg=self.colors['card']
            )
            date_label.pack(side=tk.RIGHT)
            date_label.bind("<Button-1>", on_card_click)

        # Заголовок
        title_label = tk.Label(
            content,
            text=news['title'],
            font=("Segoe UI", 12, "bold"),
            fg=self.colors['text'],
            bg=self.colors['card'],
            wraplength=320,
            justify=tk.LEFT,
            cursor="hand2"
        )
        title_label.pack(anchor=tk.W, pady=(0, 6))
        title_label.bind("<Button-1>", on_card_click)

        # Описание
        if news.get('description'):
            desc_label = tk.Label(
                content,
                text=news['description'],
                font=("Segoe UI", 10),
                fg=self.colors['text_secondary'],
                bg=self.colors['card'],
                wraplength=320,
                justify=tk.LEFT,
                cursor="hand2"
            )
            desc_label.pack(anchor=tk.W)
            desc_label.bind("<Button-1>", on_card_click)

        # ===== КНОПКИ В ПРАВОМ НИЖНЕМ УГЛУ =====
        buttons_frame = tk.Frame(content, bg=self.colors['card'])
        buttons_frame.pack(side=tk.BOTTOM, anchor='se', pady=(5, 0))

        # Кнопка перехода на сайт
        site_btn = tk.Button(
            buttons_frame,
            text="🌐",
            command=lambda url=news['link']: webbrowser.open(url),
            bg=self.colors['surface_light'],
            fg=self.colors['primary'],
            font=("Segoe UI", 12),
            bd=0,
            padx=8,
            pady=2,
            cursor="hand2"
        )
        site_btn.pack(side=tk.LEFT, padx=2)

        # Кнопка избранного
        is_fav = self.is_favorite(news['link'])
        fav_btn = tk.Button(
            buttons_frame,
            text="❤" if is_fav else "🤍",
            command=lambda n=news: self.toggle_favorite(n),
            bg=self.colors['surface_light'],
            fg=news['source_color'] if is_fav else self.colors['text_light'],
            font=("Segoe UI", 12),
            bd=0,
            padx=8,
            pady=2,
            cursor="hand2"
        )
        fav_btn.pack(side=tk.LEFT, padx=2)

        # Hover эффект для карточки
        def on_enter(e):
            if e.widget not in [site_btn, fav_btn]:
                card.configure(bg=self.colors['card_hover'])
                for child in card.winfo_children():
                    if isinstance(child, tk.Frame) and child not in [buttons_frame]:
                        child.configure(bg=self.colors['card_hover'])
                        for subchild in child.winfo_children():
                            if isinstance(subchild, tk.Frame):
                                subchild.configure(bg=self.colors['card_hover'])
                            elif isinstance(subchild, tk.Label):
                                subchild.configure(bg=self.colors['card_hover'])

        def on_leave(e):
            if e.widget not in [site_btn, fav_btn]:
                card.configure(bg=self.colors['card'])
                for child in card.winfo_children():
                    if isinstance(child, tk.Frame) and child not in [buttons_frame]:
                        child.configure(bg=self.colors['card'])
                        for subchild in child.winfo_children():
                            if isinstance(subchild, tk.Frame):
                                subchild.configure(bg=self.colors['card'])
                            elif isinstance(subchild, tk.Label):
                                subchild.configure(bg=self.colors['card'])

        card.bind("<Enter>", on_enter)
        card.bind("<Leave>", on_leave)

    def load_news_image(self, container, news):
        """Загрузка изображения для новости"""
        if news['image_url'] in self.images_cache:
            img = self.images_cache[news['image_url']]
            self.display_news_image(container, img)
            return

        def load():
            try:
                response = requests.get(news['image_url'], timeout=5)
                img_data = response.content

                pil_img = Image.open(io.BytesIO(img_data))
                # Изменяем размер под карточку
                pil_img.thumbnail((360, 150), Image.Resampling.LANCZOS)

                img = ImageTk.PhotoImage(pil_img)
                self.images_cache[news['image_url']] = img

                self.root.after(0, lambda: self.display_news_image(container, img))
            except:
                # Если не удалось загрузить, показываем плейсхолдер
                self.root.after(0, lambda: self.display_placeholder(container, news))

        thread = threading.Thread(target=load, daemon=True)
        thread.start()

    def display_news_image(self, container, img):
        """Отображение изображения в карточке"""
        for widget in container.winfo_children():
            widget.destroy()

        img_label = tk.Label(container, image=img, bg=self.colors['card'])
        img_label.image = img
        img_label.pack(fill=tk.BOTH, expand=True)

    def display_placeholder(self, container, news):
        """Отображение плейсхолдера если нет картинки"""
        for widget in container.winfo_children():
            widget.destroy()

        placeholder = tk.Frame(container, bg=self.colors['surface_light'], height=100)
        placeholder.pack(fill=tk.BOTH, expand=True)
        placeholder.pack_propagate(False)

        tk.Label(
            placeholder,
            text=news['source_icon'],
            font=("Segoe UI", 32),
            fg=self.colors['text_light'],
            bg=self.colors['surface_light']
        ).pack(expand=True)

    def toggle_favorite_from_detail(self, news):
        self.toggle_favorite(news)
        self.show_detail_panel(news)

    def filter_news(self):
        search_text = self.search_var.get().lower()

        if not search_text or search_text == "поиск новостей...":
            self.filtered_news = self.current_news
        else:
            self.filtered_news = [
                news for news in self.current_news
                if search_text in news['title'].lower() or
                   (news.get('description') and search_text in news['description'].lower())
            ]

        self.display_news()
        self.update_counters()

    def toggle_favorite(self, news):
        if self.is_favorite(news['link']):
            self.favorites = [f for f in self.favorites if f['link'] != news['link']]
        else:
            self.favorites.append(news)

        self.save_favorites()
        self.display_news()
        self.update_counters()

    def is_favorite(self, link):
        return any(f['link'] == link for f in self.favorites)

    def load_favorites(self):
        try:
            if os.path.exists('favorites.json'):
                with open('favorites.json', 'r', encoding='utf-8') as f:
                    return json.load(f)
        except:
            pass
        return []

    def save_favorites(self):
        try:
            with open('favorites.json', 'w', encoding='utf-8') as f:
                json.dump(self.favorites, f, ensure_ascii=False, indent=2)
        except:
            pass

    def update_counters(self):
        """Обновление счетчиков"""
        total = len(self.current_news)
        shown = len(self.filtered_news)
        self.news_counter.config(text=str(shown))
        self.result_counter.config(text=str(shown))

    def show_favorites(self):
        self.filtered_news = self.favorites
        self.display_news()
        self.update_info()

    def show_empty_state(self):
        empty_frame = tk.Frame(self.news_frame, bg=self.colors['bg'])
        empty_frame.pack(expand=True, fill=tk.BOTH, pady=50)

        tk.Label(
            empty_frame,
            text="📭",
            font=("Segoe UI", 48),
            fg=self.colors['text_light'],
            bg=self.colors['bg']
        ).pack()

        tk.Label(
            empty_frame,
            text="Новостей нет",
            font=("Segoe UI", 16),
            fg=self.colors['text_secondary'],
            bg=self.colors['bg']
        ).pack(pady=10)

        tk.Label(
            empty_frame,
            text="Попробуйте изменить источник\nили поисковый запрос",
            font=("Segoe UI", 11),
            fg=self.colors['text_light'],
            bg=self.colors['bg'],
            justify=tk.CENTER
        ).pack()

    def show_error(self, error):
        self.stop_loading()

        for widget in self.news_frame.winfo_children():
            widget.destroy()

        error_frame = tk.Frame(self.news_frame, bg=self.colors['bg'])
        error_frame.pack(expand=True, fill=tk.BOTH, pady=50)

        tk.Label(
            error_frame,
            text="⚠",
            font=("Segoe UI", 48),
            fg=self.colors['error'],
            bg=self.colors['bg']
        ).pack()

        tk.Label(
            error_frame,
            text="Ошибка загрузки",
            font=("Segoe UI", 16),
            fg=self.colors['text'],
            bg=self.colors['bg']
        ).pack(pady=10)

        tk.Label(
            error_frame,
            text=error,
            font=("Segoe UI", 10),
            fg=self.colors['text_secondary'],
            bg=self.colors['bg'],
            wraplength=300,
            justify=tk.CENTER
        ).pack(pady=10)

        tk.Button(
            error_frame,
            text="Повторить",
            command=self.load_news,
            bg=self.colors['primary'],
            fg='white',
            font=("Segoe UI", 12),
            bd=0,
            padx=30,
            pady=10,
            cursor="hand2"
        ).pack(pady=10)

        self.status_indicator.config(fg=self.colors['error'])

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")


def main():
    root = tk.Tk()

    # Проверяем Pillow
    try:
        from PIL import Image, ImageTk, ImageDraw
    except ImportError:
        print("Устанавливаем Pillow...")
        import subprocess
        subprocess.check_call(['pip', 'install', 'pillow'])
        from PIL import Image, ImageTk, ImageDraw

    app = KurganMobileApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()