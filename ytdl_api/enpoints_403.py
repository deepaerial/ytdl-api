import secrets

from fastapi import APIRouter, Cookie, Depends, FastAPI, HTTPException, Response
from starlette import status


def get_uid_dependency_factory(raise_error_on_empty: bool = False):
    """
    Factory function fore returning dependency that fetches client ID.
    """

    def get_uid(
        response: Response,
        uid: str | None = Cookie(None),
    ):
        """
        Dependency for fetchng user ID from cookie or setting it in cookie if absent.
        """
        if uid is None and raise_error_on_empty:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No cookie provided :(")
        elif uid is None and not raise_error_on_empty:
            uid = secrets.token_hex(16)
            response.set_cookie(
                key="uid",
                value=uid,
                samesite="None",
                secure=True,
                httponly=True,
            )
        return uid

    return get_uid


# ....
router = APIRouter(tags=["example"])


@router.get(
    "/example",
    status_code=status.HTTP_200_OK,
)
async def get_api_version(
    uid: str = Depends(get_uid_dependency_factory(raise_error_on_empty=True)),
):
    ...
    return status.HTTP_200_OK


if __name__ == "__main__":
    fastapi_app = FastAPI()
    fastapi_app.add_router(router)
