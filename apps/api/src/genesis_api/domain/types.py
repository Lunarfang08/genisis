from enum import StrEnum


class BiologicalSex(StrEnum):
    FEMALE = "female"
    MALE = "male"
    INTERSEX = "intersex"
    UNSPECIFIED = "unspecified"


class LifecycleStatus(StrEnum):
    CHILD = "child"
    ADULT = "adult"
    ELDER = "elder"
    DECEASED = "deceased"


class EducationLevel(StrEnum):
    NONE = "none"
    PRIMARY = "primary"
    SECONDARY = "secondary"
    VOCATIONAL = "vocational"
    TERTIARY = "tertiary"
    POSTGRADUATE = "postgraduate"


class EmploymentStatus(StrEnum):
    NOT_IN_WORKFORCE = "not_in_workforce"
    UNEMPLOYED = "unemployed"
    EMPLOYED = "employed"
    SELF_EMPLOYED = "self_employed"
    RETIRED = "retired"


class GoalStatus(StrEnum):
    ACTIVE = "active"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class GovernmentScope(StrEnum):
    WORLD = "world"
    REGION = "region"
    CITY = "city"


class LawStatus(StrEnum):
    PROPOSED = "proposed"
    ACTIVE = "active"
    REPEALED = "repealed"


class EventSeverity(StrEnum):
    INFO = "info"
    NOTICE = "notice"
    WARNING = "warning"
    CRITICAL = "critical"
