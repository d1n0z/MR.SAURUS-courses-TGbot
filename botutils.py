from data import db


def recursiveParentIDS(parent: int) -> list:
    cats = db.CourseCategory
    ids = [parent]
    childrens = [i for i in cats.select().where(cats.parent == parent)]
    print(childrens)
    return parentIDS(childrens, ids, cats)


def parentIDS(childrens: list[db.CourseCategory], ids, cats, k=0):
    print(k)
    for i in childrens:
        ids.append(i.id)
        childrens = [i for i in cats.select().where(cats.parent == i.id)]
        if len(childrens) > 0:
            ids = parentIDS(childrens, ids, cats, k + 1)
    return ids
