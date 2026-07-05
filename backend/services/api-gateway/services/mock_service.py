from repositories.mock_repository import MockRepository


class MockService:
    def __init__(self) -> None:
        self.repository = MockRepository()

    def get_payload(self) -> dict:
        return self.repository.get_payload()
