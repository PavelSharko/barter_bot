from enum import Enum


class UserLifecycleStatus(str, Enum):
    CONTACTED = "contacted"
    CANDIDATE = "candidate"
    CLIENT = "client"
    REJECTED = "rejected"
    BLOCKED = "blocked"

class ReviewStatus(str, Enum):
    NONE = "none"
    WAIT_REVIEW = "wait_review"
    DONE = "done"

class ProfileStatus(str, Enum):
    EMPTY = "empty"
    IN_PROGRESS = "in_progress"
    FILLED = "filled"
    SENT_TO_REVIEW = "sent_to_review"

class UserCategory(int, Enum):
    CAT_0 = 0
    CAT_25 = 25
    CAT_50 = 50
    CAT_75 = 75
    CAT_100 = 100

class UserProfile(str, Enum):
    NAME_TG = "name_tg"
    NAME_REAL = "name_real"
    DATE_REG = "date_reg"
    PHONE = "phone"
    UPDATED_AT = "updated_at"
    RULES_READ = "rules_read"
    IS_EXCLUDED = "is_excluded"
    REGION = "region"
    BALANCE = "balance"
    TOTAL_DEALS_COUNT = "total_deals_count"
    RATING_SUM = "rating_sum"
    RATING_AVG = "rating_avg"
    RULES_REMINDER_SENT_AT = "rules_reminder_sent_at"
    STATUS = "status"
    FORGOT_REVIEW_STATUS = "forgot_review_status"
    PROFILE_STATUS = "profile_status"
    CATEGORY = "category"

class Sity(str, Enum):
    BALI = "Bali"
    DUBAI = "Dubai"
    RUSSIA = "Russia"
    THAILAND = "Thailand"
