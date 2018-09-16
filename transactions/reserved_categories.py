from transactions.models import Category


class TransferCategory:
    """Category used for transactions generated from a transfer between accounts"""
    name = "transfer_sys"
    kind = Category.SYSTEM_KIND

    @classmethod
    def get_or_create(cls, **kwargs):
        defaults = {'kind': cls.kind}
        return Category.objects.get_or_create(name=cls.name, defaults=defaults, **kwargs)


class StartupAccountCategory:
    """Category used to allow accounts to start with some balance"""
    name = "startup_sys"
    kind = Category.SYSTEM_KIND

    @classmethod
    def get_or_create(cls, **kwargs):
        defaults = {'kind': cls.kind}
        return Category.objects.get_or_create(name=cls.name, defaults=defaults, **kwargs)
