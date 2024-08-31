# CutAndScale

CutAndScale is an image processing application that allows users to cut images into pieces and upscale them using AI models. This app is part of the "One time use apps" (Одноразовые приложения) project hosted at [https://onetime.bulaev.net](https://onetime.bulaev.net).

Author: Sergey Bulaev
Telegram Channel (AI-related content): [@sergiobulaev](https://t.me/sergiobulaev)
GitHub Repository: [https://github.com/chubajs/cutandscale](https://github.com/chubajs/cutandscale)
Project Website: [https://onetime.bulaev.net](https://onetime.bulaev.net)

## About the Project

CutAndScale is part of the "One time use apps" (Одноразовые приложения) project, which aims to provide simple, focused applications for specific tasks. These apps are designed to be easy to use and serve a single purpose, making them ideal for quick, one-time tasks without the need for complex software installations.

## English Instructions

### Prerequisites

1. Python 3.7 or higher
2. pip (Python package installer)

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/chubajs/cutandscale.git
   cd cutandscale
   ```

2. Create a virtual environment (optional but recommended):
   - On Windows:
     ```
     python -m venv venv
     venv\Scripts\activate
     ```
   - On macOS:
     ```
     python3 -m venv venv
     source venv/bin/activate
     ```

3. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

4. Set up your FAL API key:
   - Sign up at [fal.ai](https://fal.ai) to get an API key
   - Set the API key as an environment variable:
     - On Windows (Command Prompt):
       ```
       set FAL_KEY=your-api-key
       ```
     - On Windows (PowerShell):
       ```
       $env:FAL_KEY = "your-api-key"
       ```
     - On macOS:
       ```
       export FAL_KEY=your-api-key
       ```

### Running the Application

1. Make sure you're in the project directory and your virtual environment is activated (if you created one).

2. Run the application:
   ```
   python splitter.py
   ```

3. The application window should open. You can now:
   - Select an image
   - Cut the image into pieces
   - Upscale the entire image or the cut pieces using AI models

### Troubleshooting

- If you encounter any issues with PyQt5, try reinstalling it:
  ```
  pip uninstall PyQt5
  pip install PyQt5
  ```
- Make sure your FAL API key is correctly set as an environment variable.
- Check that all required packages are installed by running `pip freeze` and comparing with the `requirements.txt` file.

## Инструкции на русском

### О проекте

CutAndScale (Разрезать и Увеличить) - это приложение для обработки изображений, которое позволяет пользователям разрезать изображения на части и увеличивать их с помощью моделей искусственного интеллекта. Это приложение является частью проекта "Одноразовые приложения" (One time use apps), размещенного на сайте [https://onetime.bulaev.net](https://onetime.bulaev.net).

Проект "Одноразовые приложения" направлен на создание простых, узкоспециализированных приложений для конкретных задач. Эти приложения разработаны для легкого использования и выполнения одной конкретной функции, что делает их идеальными для быстрых, разовых задач без необходимости установки сложного программного обеспечения.

### Возможности CutAndScale

- Загрузка изображений
- Разрезание изображений на части с помощью настраиваемой сетки
- Увеличение масштаба всего изображения или отдельных частей с использованием двух моделей ИИ:
  - Aura SR: для высококачественного увеличения масштаба
  - Creative Upscaler: для творческого увеличения с дополнительными настройками
- Сохранение разрезанных или увеличенных изображений

### Предварительные требования

1. Python 3.7 или выше
2. pip (установщик пакетов Python)

### Установка

1. Клонируйте репозиторий:
   ```
   git clone https://github.com/chubajs/cutandscale.git
   cd cutandscale
   ```

2. Создайте виртуальное окружение (необязательно, но рекомендуется):
   - На Windows:
     ```
     python -m venv venv
     venv\Scripts\activate
     ```
   - На macOS:
     ```
     python3 -m venv venv
     source venv/bin/activate
     ```

3. Установите необходимые пакеты:
   ```
   pip install -r requirements.txt
   ```

4. Настройте ваш API ключ FAL:
   - Зарегистрируйтесь на [fal.ai](https://fal.ai), чтобы получить API ключ
   - Установите API ключ как переменную окружения:
     - На Windows (Command Prompt):
       ```
       set FAL_KEY=ваш-api-ключ
       ```
     - На Windows (PowerShell):
       ```
       $env:FAL_KEY = "ваш-api-ключ"
       ```
     - На macOS:
       ```
       export FAL_KEY=ваш-api-ключ
       ```

### Запуск приложения

1. Убедитесь, что вы находитесь в директории проекта и ваше виртуальное окружение активировано (если вы его создавали).

2. Запустите приложение:
   ```
   python splitter.py
   ```

3. Должно открыться окно приложения. Теперь вы можете:
   - Выбрать изображение
   - Разрезать изображение на части
   - Увеличить масштаб всего изображения или отдельных частей с помощью AI моделей

### Устранение неполадок

- Если у вас возникли проблемы с PyQt5, попробуйте переустановить его:
  ```
  pip uninstall PyQt5
  pip install PyQt5
  ```
- Убедитесь, что ваш API ключ FAL правильно установлен как переменная окружения.
- Проверьте, что все необходимые пакеты установлены, выполнив команду `pip freeze` и сравнив результат с файлом `requirements.txt`.
