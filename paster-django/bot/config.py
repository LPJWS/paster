import os
from vk_api.keyboard import VkKeyboard, VkKeyboardColor

def get_main_keyboard(enabled=True, is_chat=False):
    keyboard = VkKeyboard(inline=True)
    keyboard.add_button('Паста', color=VkKeyboardColor.PRIMARY)
    keyboard.add_button('Случайная паста', color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button('ТОП', color=VkKeyboardColor.PRIMARY)
    keyboard.add_button('ТОП Участников', color=VkKeyboardColor.PRIMARY)
    if is_chat:
        keyboard.add_line()
        keyboard.add_button(
            'Отключить уведомления' if enabled else 'Включить уведомления', 
            color=VkKeyboardColor.POSITIVE if enabled else VkKeyboardColor.NEGATIVE)
    return keyboard.get_keyboard()

def get_enable_keyboard():
    keyboard = VkKeyboard(inline=True)
    keyboard.add_button('Отключить уведомления', color=VkKeyboardColor.PRIMARY)
    return keyboard.get_keyboard()

service = os.environ.get('VK_SERVICE')
token = os.environ.get('VK_TOKEN')
group_id = os.environ.get('VK_GROUP_ID')
main_keyboard = get_main_keyboard()
groups = ['108531402', '92157416', '157651636']
groups_minus = [-int(i) for i in groups]
marks_keys = {'1️⃣⭐️': 1, '2️⃣⭐️': 2, '3️⃣⭐️': 3, '4️⃣⭐️': 4, '5️⃣⭐️': 5}
marks_keys_inv = {v: k for k, v in marks_keys.items()}
