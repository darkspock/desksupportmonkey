from datetime import time, date
from unittest.mock import MagicMock

import pytest

from src.appointment_bc.appointment.application.commands.set_availability import (
    AvailabilityWindowInput,
    SetAvailabilityCommand,
    SetAvailabilityCommandHandler,
)
from src.appointment_bc.appointment.application.commands.add_override import (
    AddOverrideCommand,
    AddOverrideCommandHandler,
)
from src.appointment_bc.appointment.application.commands.delete_override import (
    DeleteOverrideCommand,
    DeleteOverrideCommandHandler,
    OverrideNotFoundError,
)


class TestSetAvailability:

    def test_set_availability_saves_all(self):
        repo = MagicMock()
        handler = SetAvailabilityCommandHandler(
            availability_repo=repo,
        )
        handler.handle(
            SetAvailabilityCommand(
                technician_id="tech1",
                company_id="comp1",
                windows=[
                    AvailabilityWindowInput(
                        day_of_week=0,
                        start_time=time(9, 0),
                        end_time=time(12, 0),
                    ),
                    AvailabilityWindowInput(
                        day_of_week=0,
                        start_time=time(14, 0),
                        end_time=time(17, 0),
                    ),
                ],
            )
        )
        repo.save_all.assert_called_once()
        args = repo.save_all.call_args
        assert args.kwargs["technician_id"] == "tech1"
        assert args.kwargs["company_id"] == "comp1"
        assert len(args.kwargs["windows"]) == 2

    def test_set_availability_validates_windows(self):
        repo = MagicMock()
        handler = SetAvailabilityCommandHandler(
            availability_repo=repo,
        )
        with pytest.raises(ValueError):
            handler.handle(
                SetAvailabilityCommand(
                    technician_id="tech1",
                    company_id="comp1",
                    windows=[
                        AvailabilityWindowInput(
                            day_of_week=7,
                            start_time=time(9, 0),
                            end_time=time(12, 0),
                        ),
                    ],
                )
            )
        repo.save_all.assert_not_called()

    def test_set_availability_empty_windows(self):
        repo = MagicMock()
        handler = SetAvailabilityCommandHandler(
            availability_repo=repo,
        )
        handler.handle(
            SetAvailabilityCommand(
                technician_id="tech1",
                company_id="comp1",
                windows=[],
            )
        )
        repo.save_all.assert_called_once()
        assert len(
            repo.save_all.call_args.kwargs["windows"],
        ) == 0


class TestAddOverride:

    def test_add_override_block(self):
        repo = MagicMock()
        handler = AddOverrideCommandHandler(
            override_repo=repo,
        )
        handler.handle(
            AddOverrideCommand(
                override_id="ovr1",
                company_id="comp1",
                technician_id="tech1",
                target_date=date(2026, 3, 15),
                is_available=False,
                reason="Vacation",
            )
        )
        saved = repo.save.call_args[0][0]
        assert saved.id == "ovr1"
        assert saved.is_available is False
        assert saved.reason == "Vacation"

    def test_add_override_extra(self):
        repo = MagicMock()
        handler = AddOverrideCommandHandler(
            override_repo=repo,
        )
        handler.handle(
            AddOverrideCommand(
                override_id="ovr2",
                company_id="comp1",
                technician_id="tech1",
                target_date=date(2026, 3, 16),
                is_available=True,
                start_time=time(10, 0),
                end_time=time(14, 0),
            )
        )
        saved = repo.save.call_args[0][0]
        assert saved.is_available is True
        assert saved.start_time == time(10, 0)
        assert saved.end_time == time(14, 0)

    def test_add_override_validates_times(self):
        repo = MagicMock()
        handler = AddOverrideCommandHandler(
            override_repo=repo,
        )
        with pytest.raises(ValueError):
            handler.handle(
                AddOverrideCommand(
                    override_id="ovr3",
                    company_id="comp1",
                    technician_id="tech1",
                    target_date=date(2026, 3, 17),
                    is_available=True,
                )
            )
        repo.save.assert_not_called()


class TestDeleteOverride:

    def test_delete_override_succeeds(self):
        repo = MagicMock()
        repo.delete.return_value = True
        handler = DeleteOverrideCommandHandler(
            override_repo=repo,
        )
        handler.handle(
            DeleteOverrideCommand(
                override_id="ovr1",
                company_id="comp1",
            )
        )
        repo.delete.assert_called_once_with(
            "ovr1", "comp1",
        )

    def test_delete_override_not_found_raises(self):
        repo = MagicMock()
        repo.delete.return_value = False
        handler = DeleteOverrideCommandHandler(
            override_repo=repo,
        )
        with pytest.raises(OverrideNotFoundError):
            handler.handle(
                DeleteOverrideCommand(
                    override_id="bad_id",
                    company_id="comp1",
                )
            )
