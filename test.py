from lxml import etree

def find_common_parent(html_content, xpaths):
    # Парсим HTML-документ
    parser = etree.HTMLParser()
    tree = etree.fromstring(html_content, parser)

    # Создаем список элементов для каждого XPath
    elements = [tree.xpath(xpath) for xpath in xpaths]
    print(elements)
    # Находим общего родителя для всех элементов
    common_parent = None
    for el_set in zip(*elements):
        if all(el.getroottree() == el_set[0].getroottree() for el in el_set):
            common_parent = el_set[0].getroottree().getpath(el_set[0])
            break

    return common_parent

# Пример использования
html_content = """
<html>
<body>
<div>
    <p>Text 1</p>
    <p>Text 2</p>
</div>
<div>
    <p>Text 3</p>
    <p>Text 4</p>
</div>
</body>
</html>
"""

xpaths = ["/html/body/div[1]/p", "/html/body/div[2]/p"]
common_parent = find_common_parent(html_content, xpaths)
print("Минимальный общий родитель:", common_parent)
