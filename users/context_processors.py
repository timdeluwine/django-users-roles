def admin_access(request):
    """Предоставляет флаг is_admin_user в шаблоны по тем же правилам,

    что и AdminRequiredMixin: только суперпользователь или участник группы 'admin'.
    """
    if not request.user.is_authenticated:
        return {"is_admin_user": False}

    return {
        "is_admin_user": request.user.is_superuser
        or request.user.groups.filter(name="admin").exists()
    }
