class TicketNotFoundError(Exception):
    pass


class InvalidTicketTransitionError(Exception):
    pass


class TicketReopenWindowExpiredError(Exception):
    pass


class TicketAlreadyRatedError(Exception):
    pass


class TicketRatingNotAllowedError(Exception):
    pass
