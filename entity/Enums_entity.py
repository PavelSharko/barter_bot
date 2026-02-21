from enum import Enum


class UserLifecycleStatus(str, Enum):
    CONTACTED = "contacted" #это те кто зарегался но анкету еше не отправил на проверку 
    CANDIDATE = "candidate" #это те кто  анкету  отправил на проверку 
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

class UserFields(str, Enum):
    NAME_TG = "name_tg"
    NAME_REAL = "name_real"
    DATE_REG = "date_reg"
    PHONE = "phone"
    UPDATED_AT = "updated_at"
    REGION = "region"
    RULES_REMINDER_SENT_AT = "rules_reminder_sent_at"
    STATUS = "status"
    FORGOT_REVIEW_STATUS = "forgot_review_status"
    PROFILE_STATUS = "profile_status"
    CATEGORY = "category"
    BLOCK_PROFILE_INFO_REASON = "block_anketa_reason"
    REASON_FOR_BLOCKING_USER = "user_block_reason"

class BlockingStatusFields(str, Enum):
    BLOCK_ID = "block_id"
    USER_ID = "user_id"
    MODERATOR_ID = "moderator_id"
    REASON = "reason"
    CREATED_AT = "created_at"
    STATUS_BEFORE = "status_before"
    STATUS_AFTER = "status_after"

class UserFlags(str, Enum):
    RULES_READ = "rules_read"
    IS_EXCLUDED = "is_excluded"
    CHANGES_PROFILE_CONFIRMED = "changes_profile_confirmed"

class ChangesProfileStatus(str, Enum):
    WAITING_CONFIRMATION = "waiting_confirmation" 
    CONFIRMED = "confirmed"
    NOT_CHANGES = "not_changes" 
    PENDING_CHANGES = "pending_changes"

    


class UserMetrics(str, Enum):
    BALANCE = "balance"
    TOTAL_DEALS_COUNT = "total_deals_count"
    RATING_SUM = "rating_sum"
    RATING_AVG = "rating_avg"

class Sity(str, Enum):
    BALI = "Bali"
    DUBAI = "Dubai"
    RUSSIA = "Russia"
    THAILAND = "Thailand"

class UserProfileFields(str, Enum):
    NAME = "name"
    AREA = "area"
    SERVICE_NAME = "service_name"
    SERVICE_DESCRIPTION = "service_description"
    PRICE_INFO = "price_info"
    SOCIAL_LINKS = "social_links"
    CURRENT_STEP = "current_step"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"
    VERSION = "version"
