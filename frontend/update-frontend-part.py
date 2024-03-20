import os
import glob
import shutil

# Запускаем npm run build в директории Dialobild-Frontend
if os.path.basename(os.getcwd()) != 'Dialobild-Frontend':
    os.chdir('Dialobild-Frontend')
os.system('npm run build')

# Получаем список файлов в директории
js_files = glob.glob('build/static/js/*.js')

# Копируем файлы в нужную директорию
for file in js_files:
    shutil.copy(file, '../static/frontend/js/dialobild-app.js')

# Получаем список файлов в директории
css_files = glob.glob('build/static/css/*.css')

# Копируем файлы в нужную директорию
for file in js_files:
    shutil.copy(file, '../static/frontend/css/dialobild-app.css')