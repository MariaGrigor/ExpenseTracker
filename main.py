"""
БИЗНЕС-ПРИЛОЖЕНИЕ: Трекер расходов для малого бизнеса
Цель: демонстрация быстрой разработки кроссплатформенного приложения
Для студентов направления "Бизнес-информатика"

ВАЖНО: Запускайте этот скрипт как обычный файл Python (например, `python main.py`).
Не запускайте его внутри Jupyter Notebook, REPL или других интерактивных сред,
так как это вызовет ошибку `OSError: source code not available`.
"""

import json
import os
from datetime import datetime
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.properties import StringProperty, NumericProperty, BooleanProperty
from kivy.uix.recycleview import RecycleView
from kivy.uix.behaviors import FocusBehavior
from kivy.uix.recycleview.layout import LayoutSelectionBehavior
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.storage.jsonstore import JsonStore
from kivy.lang import Builder

# Загружаем KV язык для описания интерфейса
Builder.load_string('''
#:import Factory kivy.factory.Factory

<ExpenseRow>:
    canvas.before:
        Color:
            rgba: (0.9, 0.9, 0.9, 1) if self.selected else (1, 1, 1, 1)
        Rectangle:
            pos: self.pos
            size: self.size
    orientation: 'horizontal'
    padding: 10
    height: 60
    
    Label:
        text: root.category
        size_hint_x: 0.3
        color: 0, 0, 0, 1

    Label:
        text: root.description
        size_hint_x: 0.4
        color: 0, 0, 0, 1

    Label:
        text: str(root.amount) + ' руб.'
        size_hint_x: 0.3
        color: (0, 0.6, 0, 1) if root.operation_type == 'income' else (1, 0, 0, 1)

<ExpensesRV>:
    viewclass: 'ExpenseRow'
    RecycleBoxLayout:
        default_size: None, dp(60)
        default_size_hint: 1, None
        size_hint_y: None
        height: self.minimum_height
        orientation: 'vertical'

<MainScreen>:
    BoxLayout:
        orientation: 'vertical'
        padding: 20
        spacing: 10

        Label:
            text: 'БИЗНЕС-ТРЕКЕР РАСХОДОВ'
            font_size: 24
            bold: True
            color: 0.2, 0.4, 0.8, 1
            size_hint_y: 0.1

        BoxLayout:
            orientation: 'horizontal'
            size_hint_y: 0.15

            Button:
                text: 'Добавить расход'
                on_press: root.show_add_expense_popup()
                background_color: 0.2, 0.6, 0.2, 1


            Button:
                text: 'Добавить доход'
                on_press: root.show_add_income_popup()
                background_color: 0.2, 0.5, 0.7, 1


            Button:
                text: 'Аналитика'
                on_press: root.show_analytics()
                background_color: 0.3, 0.3, 0.7, 1

            Button:
                text: 'Экспорт'
                on_press: root.export_data()
                background_color: 0.7, 0.5, 0.2, 1

        Label:
            text: 'Общий расход: ' + str(root.total_expenses) + ' руб.'
            font_size: 18
            bold: True
            color: 1, 0, 0, 1
            size_hint_y: 0.08

        Label:
            text: 'Общий доход: ' + str(root.total_income) + ' руб.'
            font_size: 18
            bold: True
            color: 0, 1, 0, 1
            size_hint_y: 0.08

        Label:
            text: 'Баланс: ' + str(root.balance) + ' руб.'
            font_size: 18
            bold: True
            color: 1, 1, 1, 1
            size_hint_y: 0.08


        ExpensesRV:
            id: rv
            size_hint_y: 0.51

<AddExpensePopup>:
    size_hint: 0.8, 0.6
    title: 'Добавить новый расход'
    BoxLayout:
        orientation: 'vertical'
        padding: 20
        spacing: 10

        Label:
            text: 'Категория:'

        Spinner:
            id: category_spinner
            text: 'Выберите категорию'
            values: ['Офис', 'Зарплаты', 'Маркетинг', 'Логистика', 'Налоги', 'Прочее']
            size_hint_y: 0.15

        Label:
            text: 'Описание:'

        TextInput:
            id: description_input
            multiline: False
            size_hint_y: 0.15

        Label:
            text: 'Сумма (руб.):'

        TextInput:
            id: amount_input
            multiline: False
            input_filter: 'float'
            size_hint_y: 0.15

        BoxLayout:
            orientation: 'horizontal'
            spacing: 10
            size_hint_y: 0.2

            Button:
                text: 'Отмена'
                on_press: root.dismiss()
                background_color: 0.8, 0.2, 0.2, 1

            Button:
                text: 'Сохранить'
                on_press: root.save_expense()
                background_color: 0.2, 0.6, 0.2, 1

<AddIncomePopup>:
    size_hint: 0.8, 0.6
    title: 'Добавить доход'

    BoxLayout:
        orientation: 'vertical'
        padding: 20
        spacing: 10

        Label:
            text: 'Категория дохода:'

        Spinner:
            id: category_spinner
            text: 'Выберите категорию'
            values: ['Продажи', 'Услуги', 'Прочее']
            size_hint_y: 0.15

        Label:
            text: 'Описание:'

        TextInput:
            id: description_input
            multiline: False
            size_hint_y: 0.15

        Label:
            text: 'Сумма (руб.):'

        TextInput:
            id: amount_input
            multiline: False
            input_filter: 'float'
            size_hint_y: 0.15

        BoxLayout:
            orientation: 'horizontal'
            spacing: 10
            size_hint_y: 0.2

            Button:
                text: 'Отмена'
                on_press: root.dismiss()

            Button:
                text: 'Сохранить'
                on_press: root.save_income()
''')

# --- Бизнес-логика и модели данных ---

class ExpenseRow(RecycleDataViewBehavior, BoxLayout):
    """Модель строки расхода для RecycleView"""
    category = StringProperty('')
    description = StringProperty('')
    amount = NumericProperty(0)
    operation_type = StringProperty('expense')
    selected = BooleanProperty(False)
    index = None

    def refresh_view_attrs(self, rv, index, data):
        """Обновление вида при изменении данных"""
        self.index = index
        return super().refresh_view_attrs(rv, index, data)


class SelectableRecycleBoxLayout(FocusBehavior, LayoutSelectionBehavior, BoxLayout):
    """Наследование для возможности выбора в RecycleView"""


class ExpensesRV(RecycleView):
    """Виджет для отображения списка расходов"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


# --- Экран приложения ---

class MainScreen(Screen):
    """Главный экран приложения"""
    total_expenses = NumericProperty(0) #total_expenses — общая сумма расходов (уже была)
    total_income = NumericProperty(0) #total_income — общая сумма доходов (новая)
    balance = NumericProperty(0) #balance — разница между доходами и расходами (новая)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.store = JsonStore('expenses.json')
        self.load_expenses()


    def load_expenses(self):
        """Загрузка операций и расчет баланса"""
        expenses = []
        total_expenses = 0
        total_income = 0

        for key in self.store.keys():
            operation = self.store.get(key)
            amount = float(operation.get('amount', 0))

            # Старые записи считаются расходами
            operation_type = operation.get('type', 'expense')

            if operation_type == 'income':
                total_income += amount
            else:
                total_expenses += amount

            expenses.append({
                'category': operation.get('category', ''),
                'description': operation.get('description', ''),
                'amount': amount,
                'operation_type': operation_type
            })

        self.ids.rv.data = expenses
        self.total_expenses = total_expenses
        self.total_income = total_income
        self.balance = total_income - total_expenses


    def show_add_expense_popup(self):
        """Показать попап добавления расхода"""
        popup = AddExpensePopup(main_screen=self)
        popup.open()

    def show_add_income_popup(self):
        """Открытие формы добавления дохода"""
        popup = AddIncomePopup(main_screen=self)
        popup.open()

    def add_expense(self, category, description, amount):
        """Добавление нового расхода (бизнес-логика)"""
        try:
            amount = float(amount)
            expense = {
                'category': category,
                'description': description,
                'amount': amount,
                'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

            key = f"expense_{datetime.now().timestamp()}"
            self.store.put(key, **expense)
            self.load_expenses()

        except ValueError:
            self.show_error_popup("Ошибка", "Введите корректную сумму")


    def add_income(self, category, description, amount):
        """Сохранение дохода"""
        income = {
            'type': 'income',
            'category': category,
            'description': description,
            'amount': amount,
            'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        key = f"income_{datetime.now().timestamp()}"
        self.store.put(key, **income)
        self.load_expenses()

    def show_analytics(self):
        """Показать аналитику расходов (заглушка)"""
        categories = {}
        for expense in self.ids.rv.data:
            cat = expense['category']
            categories[cat] = categories.get(cat, 0) + expense['amount']

        content = BoxLayout(orientation='vertical', padding=10)
        for category, total in categories.items():
            content.add_widget(Label(
                text=f"{category}: {total} руб.",
                font_size=16
            ))

        popup = Popup(
            title='Аналитика расходов по категориям',
            content=content,
            size_hint=(0.8, 0.6)
        )
        popup.open()

    def export_data(self):
        """Экспорт данных в CSV (демонстрация бизнес-функции)"""
        import csv

        try:
            with open('expenses_export.csv', 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['Категория', 'Описание', 'Сумма', 'Дата'])

                for key in self.store.keys():
                    expense = self.store.get(key)
                    writer.writerow([
                        expense['category'],
                        expense['description'],
                        expense['amount'],
                        expense.get('date', '')
                    ])

            self.show_error_popup("Успех", "Данные экспортированы в expenses_export.csv")
        except Exception as e:
            self.show_error_popup("Ошибка", str(e))

    def show_error_popup(self, title, message):
        """Утилита для показа ошибок"""
        popup = Popup(
            title=title,
            content=Label(text=message),
            size_hint=(0.6, 0.4)
        )
        popup.open()


class AddExpensePopup(Popup):
    """Попап для добавления расхода"""
    def __init__(self, main_screen, **kwargs):
        super().__init__(**kwargs)
        self.main_screen = main_screen

    def save_expense(self):
        """Сохранение расхода"""
        category = self.ids.category_spinner.text
        description = self.ids.description_input.text
        amount = self.ids.amount_input.text

        if category == 'Выберите категорию':
            self.main_screen.show_error_popup("Ошибка", "Выберите категорию")
            return

        if not description or not amount:
            self.main_screen.show_error_popup("Ошибка", "Заполните все поля")
            return

        self.main_screen.add_expense(category, description, amount)
        self.dismiss()


class AddIncomePopup(Popup):
    """Форма добавления дохода"""

    def __init__(self, main_screen, **kwargs):
        super().__init__(**kwargs)
        self.main_screen = main_screen

    def save_income(self):
        category = self.ids.category_spinner.text
        description = self.ids.description_input.text.strip()
        amount = self.ids.amount_input.text

        if category == 'Выберите категорию':
            self.main_screen.show_error_popup(
                "Ошибка", "Выберите категорию"
            )
            return

        if not description or not amount:
            self.main_screen.show_error_popup(
                "Ошибка", "Заполните все поля"
            )
            return

        try:
            amount = float(amount)
        except ValueError:
            self.main_screen.show_error_popup(
                "Ошибка", "Введите корректную сумму"
            )
            return

        if not 0 < amount < float('inf'):
            self.main_screen.show_error_popup(
                "Ошибка", "Сумма должна быть положительной"
            )
            return

        self.main_screen.add_income(category, description, amount)
        self.dismiss()


# --- Основное приложение ---

class ExpenseTrackerApp(App):
    """Основной класс приложения"""
    def build(self):
        """Сборка интерфейса приложения"""
        self.title = "Business Expense Tracker"
        self.icon = 'icon.png'

        sm = ScreenManager()
        sm.add_widget(MainScreen(name='main'))
        return sm

    def on_pause(self):
        """Обработка паузы на мобильных устройствах"""
        return True

    def on_resume(self):
        """Обработка возобновления работы"""
        pass


# --- Точка входа ---
if __name__ == '__main__':
    ExpenseTrackerApp().run()
