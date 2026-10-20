from mozilla_django_oidc.auth import OIDCAuthenticationBackend


class KeycloakOIDCAuthenticationBackend(OIDCAuthenticationBackend):
    """Авторизация через Keycloak с извлечением claims напрямую из JWT payload."""

    def get_userinfo(self, access_token, id_token, payload):
        return payload

    def create_user(self, claims):
        username = claims.get("preferred_username") or claims.get("email") or claims.get("sub")
        email = claims.get("email", "")
        user = self.UserModel.objects.create_user(username=username, email=email)
        user.first_name = claims.get("given_name", "")
        user.last_name = claims.get("family_name", "")
        user.save()
        return user

    def update_user(self, user, claims):
        user.first_name = claims.get("given_name", user.first_name)
        user.last_name = claims.get("family_name", user.last_name)
        user.email = claims.get("email", user.email)
        user.save()
        return user
