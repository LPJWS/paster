import os
from vk_api.keyboard import VkKeyboard, VkKeyboardColor

def get_main_keyboard():
    keyboard = VkKeyboard(inline=True)
    keyboard.add_button('Паста', color=VkKeyboardColor.PRIMARY)
    keyboard.add_button('Случайная паста', color=VkKeyboardColor.PRIMARY)
    return keyboard.get_keyboard()

service = os.environ.get('VK_SERVICE')
token = os.environ.get('VK_TOKEN')
group_id = 207290394
main_keyboard = get_main_keyboard()
groups = ['108531402', '92157416']
groups_minus = [-int(i) for i in groups]
