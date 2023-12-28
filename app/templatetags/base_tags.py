from django import template

register = template.Library()

@register.filter(name='mention')
def mention(title, data):
    return f"""
        <strong class="m-0">{title}</strong>
        <span class="mb-3">{data.participant} gave a {data.score} average score</span>
    """

@register.filter(name='stat')
def stat(title, id, value):
    return f"""
        <p>{title}: <span id="{id}">{value}</span></p>
    """
