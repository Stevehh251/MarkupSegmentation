from lxml import html, etree
from bs4 import BeautifulSoup

def xpath_soup(element):
    '''
        This function generate xpath from BeautifulSoup4 element.
        This was adapted from a gist from Felipe A. Hernandez to a GitHub:
        https://gist.github.com/ergoithz/6cf043e3fdedd1b94fcf
    '''
    components = []
    child = element if element.name else element.parent
    for parent in child.parents:
        siblings = parent.find_all(child.name, recursive=False)
        components.append(
            child.name if 1 == len(siblings) else '%s[%d]' % (
                child.name,
                next(i for i, s in enumerate(siblings, 1) if s is child)
            )
        )
        child = parent
    components.reverse()
    return '/%s' % '/'.join(components)


def generate_all_xpaths(html: str):
    soup = BeautifulSoup(html, 'html.parser')
    elems = soup.find_all()
    xpaths = []
    for elem in elems:
        xpaths.append(xpath_soup(elem))

    return xpaths



def print_elements(element, indent=0):
    '''
        Beautiful print for subtree
    '''
    print(' ' * indent + element.tag + ' ' + str(element))
    for child in element:
        print_elements(child, indent + 4)


def get_children_elements(element):
    '''
        This function returns set of all children for specified element
    '''
    all_elems = set(element)
    for child in element:
        all_elems = all_elems.union(get_children_elements(child))

    return all_elems


def find_xpath_segment(html: str, xpaths: list, target_xpath: str):
    '''
        This function can return biggest uncommon parent for target_xpath
    '''

    parser = etree.HTMLParser()
    tree = etree.fromstring(html, parser)

    elements = set()
    for xpath in xpaths:
        elements.add(tree.xpath(xpath)[0])

    answer = None

    element = tree.xpath(target_xpath)[0]
    # print("elem : ", element)
    # Находим всех родителей элемента
    parents = element.iterancestors()
    for parent in parents:
        childrens = get_children_elements(parent)
        inter = childrens.intersection(elements)
        # print()
        # print(parent, " : ", childrens)
        # print(parent, " : ", elements)
        # print()
        if len(inter) == 1:
            answer = parent

    return answer  # Если не найдено подходящего родителя


def generate_segmentation(html: str, xpaths: list):
    '''
        This function generates segmentation for each xpath in xpaths
    '''
    segments = set()

    for xpath in xpaths:
        segment = find_xpath_segment(html, xpaths, xpath)
        segments.add(segment)

    return xpaths


# Пример использования

# unique_parent = find_xpath_segment(html, xpaths, xpaths[1])
# # print('\n')
# if unique_parent is not None:
#     print(etree.tostring(unique_parent, encoding='unicode'))
# else:
#     print("Максимальный родитель не найден.")

# parser = etree.HTMLParser()
# print(etree.tostring(etree.fromstring(html, parser).xpath("/html/body/div[2]")[0], encoding='unicode'))

# print(list(generate_segmentation(html, xpaths)))


def str_prefix(parsed_string: list, prefix: int):
    return "/".join(parsed_string[:prefix])


def generate_segmentation_str(xpaths: list):
    '''
        Эта функция берет список строк xpath и для каждого xpath находит такой минимальный префикс,
        что он не содержит других элементов списка
    '''
    xpaths = [xpath.split('/') for xpath in xpaths]
    unique_xpaths = []

    for xpath in xpaths:
        for prefix_len in range(1, len(xpath)):
            prefix = str_prefix(xpath, prefix_len)

            unique_prefix = True

            for other_xpath in xpaths:
                if other_xpath != xpath:
                    other_prefix = str_prefix(other_xpath, prefix_len)

                    if other_prefix == prefix:
                        unique_prefix = False
                        break

            if unique_prefix:
                unique_xpaths.append(prefix)
                break
        else:
            prefix = str_prefix(xpath, None)
            unique_xpaths.append(prefix)
            break

    return unique_xpaths


# segments = generate_segmentation_str(xpaths)

# for i in range(len(segments)):
#     print(xpaths[i], segments[i])


def path_contains(x: list, y: list):
    '''
        True if x contains y
    '''
    return x == y[:len(x)]


def path_intersection(x: list, y: list, all_xpath: list):
    '''
        return all xpaths contains in x and y
    '''
    intersection = []
    for xpath in all_xpath:
        if path_contains(x, xpath) and path_contains(y, xpath):
            intersection.append(xpath)

    return intersection


def path_minus(x: list, y: list, all_xpath: list):
    '''
        return x \ y = x & (!y)
    '''
    minus = []
    for xpath in all_xpath:
        if path_contains(x, xpath) and (not path_contains(y, xpath)):
            minus.append(xpath)

    return minus


def make_scores(segments_true: list, segments_pred: list, all_xpaths: list):
    '''
        Сначала нужно как-то сопоставить узлы
        Так как нумерация может отличаться
        Для этого найдем для каждого правильного узла
        предсказанный узел, в который он попадает
    '''
    all_xpaths = [xpath.split('/') for xpath in all_xpaths]
    segments_true = [true_segment.split('/') for true_segment in segments_true]
    segments_pred = [predict.split('/') for predict in segments_pred]

    segment_scores = []
    for true_segment in segments_true:
        for predict in segments_pred:
            if path_contains(predict, true_segment):
                TP = len(path_intersection(predict, true_segment, all_xpaths))
                FP = len(path_minus(predict, true_segment, all_xpaths))
                FN = len(path_minus(true_segment, predict, all_xpaths))
                segment_scores.append({"TP": TP,
                                       "FP": FP,
                                       "FN": FN})
                break
        else:
            segment_scores.append({"TP": 0,
                                   "FP": 0,
                                   "FN": 0})

    return segment_scores

# Из Dataset
html = """
<html>
<body>
<div>
    <p id="unique1">Уникальный параграф 1</p>
</div>
<div>
    <div>
        <p id="unique2">Уникальный параграф 2</p>
    </div>
</div>
<p id="unique3">Уникальный параграф 3</p>
</body>
</html>
"""
# Из Markup
predicted_xpaths = ["/html/body/div[1]/p", "/html/body/div[2]/div/p"]
# Из Dataset
labeled_xpaths = ["/html/body/div[1]/p", "/html/body/div[2]/div/p", "/html/body/p"]
# Пример использования

print(make_scores(
    generate_segmentation_str(labeled_xpaths),
    generate_segmentation_str(predicted_xpaths),
    generate_all_xpaths(html)
))

class segmentation_metric():
    def __inti__(self):
        self.scores = []
        
    def add_result(self, item: dict):
        scores = make_scores(
            generate_segmentation_str(item["true_xpaths"]),
            generate_segmentation_str(item["pred_xpaths"]),
            generate_all_xpaths(item["html"])
        )
        
        self.scores += scores
    
    def precision(item: dict):
        return item["TP"] / (item["TP"] + item["FP"])
    
    def recall(item: dict):
        return item["TP"] / (item["TP"] + item["FN"])

    def avg_precision(precisions: list):
        return sum(precisions) / len(precisions)
    
    def avg_recall(recalls: list):
        return sum(recalls) / len(recalls)

    def avg_f1(avg_recall, avg_precision):
        return 2 * (avg_precision * avg_recall) / (avg_precision * avg_recall)
        
    def get_metric(self):
        avg_precision = self.avg_precision(self.scores)
        avg_recall = self.avg_recall(self.scores)
        avg_f1 = self.avg_f1(avg_recall=avg_recall, 
                             avg_precision=avg_precision)
        
        return {"avg_precision" : avg_precision,
                "avg_recall": avg_recall,
                "avg_f1": avg_f1}

    