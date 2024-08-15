import os

DB_NAME = 'database.db'
DB_PATH = os.path.join(os.path.dirname(__file__), DB_NAME)

ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'admin123'

TOTAL_LEAVES_PER_YEAR = 20

COLORSCHEME = {
    'primary': '#1E88E5',
    'secondary': '#FFC107',
    'background': '#0e1117',
    'text': '#333333',
    'success': '#4CAF50',
    'danger': '#F44336',
    'warning': '#FF9800',
    'info': '#2196F3'
}
# COLORSCHEME = {
#     'primary': '#1E88E5',
#     'secondary': '#FFC107',
#     'background': '#F3F4F6',
#     'text': '#333333',
#     'success': '#4CAF50',
#     'danger': '#F44336',
#     'warning': '#FF9800',
#     'info': '#2196F3'
# }