from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Literal, Required, TypeAlias, TypedDict

EmulateMediaType = Literal["screen", "print"]
WaitUntil = Literal["load", "domcontentloaded", "networkidle", "commit"]
PaperFormat = Literal[
    "Letter",
    "Legal",
    "Tabloid",
    "Ledger",
    "A0",
    "A1",
    "A2",
    "A3",
    "A4",
    "A5",
    "A6",
]
ContentDisposition = Literal["inline", "attachment"]
CompressionLevel = Literal["lossless", "low", "medium", "high"]
SyncConversionStatus = Literal["SUCCESS"]
AsyncConversionWebhookStatus = Literal["SUCCESS", "FAILURE"]
ConversionErrorCode: TypeAlias = (
    Literal[
        "BAD_REQUEST",
        "UNAUTHORIZED",
        "FORBIDDEN",
        "NOT_FOUND",
        "PAYLOAD_TOO_LARGE",
        "PDF_SIZE_TOO_LARGE",
        "TEMPLATE_EVAL_ERROR",
        "TOO_MANY_REQUESTS",
        "UNPROCESSABLE_ENTITY",
        "SERVICE_UNAVAILABLE",
        "GATEWAY_TIMEOUT",
        "CUSTOM_S3_UPLOAD_ERROR",
        "TARGET_CLOSED",
        "NO_BROWSER_CONTEXT",
        "URL_NOT_RESOLVED",
        "PDF_PRINTING_FAILED",
        "CONVERSION_TIMEOUT",
        "UNEXPECTED_ERROR",
        "INVALID_CREDENTIALS",
        "HTTP_RESPONSE_FAILURE",
        "CLIENT_DISCONNECTED",
    ]
    | str
)
PageDimension = int | float | str
MarginDimension = int | float | str


class HttpCredentials(TypedDict):
    username: str
    password: str


class ViewportSize(TypedDict):
    width: int
    height: int


class CookieOptions(TypedDict, total=False):
    expires: int | float | None
    http_only: bool | None
    secure: bool | None


class UrlCookie(CookieOptions):
    name: Required[str]
    value: Required[str]
    url: Required[str]


class DomainCookie(CookieOptions):
    name: Required[str]
    value: Required[str]
    domain: Required[str]
    path: Required[str]


PDFBoltCookie = UrlCookie | DomainCookie


class WaitForSelector(TypedDict):
    selector: str
    state: Literal["attached", "detached", "visible", "hidden"]


class Margin(TypedDict, total=False):
    top: MarginDimension | None
    right: MarginDimension | None
    bottom: MarginDimension | None
    left: MarginDimension | None


class PrintProduction(TypedDict, total=False):
    pdf_standard: Literal["pdf-x-4", "pdf-x-1a"] | None
    color_space: Literal["rgb", "cmyk"] | None
    icc_profile: Literal["fogra39", "fogra51", "swop", "gracol"] | None
    preserve_black: bool | None


class ConversionOptions(TypedDict, total=False):
    emulate_media_type: EmulateMediaType | None
    java_script_enabled: bool | None
    http_credentials: HttpCredentials | None
    viewport_size: ViewportSize | None
    is_mobile: bool | None
    device_scale_factor: int | float | None
    extra_http_headers: Mapping[str, str] | None
    apply_extra_http_headers_to_all_resources: bool | None
    cookies: list[PDFBoltCookie] | None
    wait_until: WaitUntil | None
    wait_for_function: str | None
    wait_for_selector: WaitForSelector | None
    timeout: int | float | None
    format: PaperFormat | None
    landscape: bool | None
    width: PageDimension | None
    height: PageDimension | None
    margin: Margin | None
    page_ranges: str | None
    prefer_css_page_size: bool | None
    print_background: bool | None
    scale: int | float | None
    display_header_footer: bool | None
    header_template: str | None
    footer_template: str | None
    tagged: bool | None
    print_production: PrintProduction | None
    content_disposition: ContentDisposition | None
    filename: str | None
    compression: CompressionLevel | None
    request_timeout: int | float | None


class DirectOptions(ConversionOptions, total=False):
    is_encoded: bool | None


class SyncOptions(ConversionOptions, total=False):
    custom_s3_presigned_url: str | None


class AsyncOptions(ConversionOptions, total=False):
    custom_s3_presigned_url: str | None
    additional_webhook_headers: Mapping[str, str] | None
    retry_delays: list[int] | None


class DirectUrlParams(DirectOptions):
    url: Required[str]


class DirectHtmlParams(DirectOptions):
    html: Required[str]


class DirectTemplateParams(DirectOptions):
    template_id: Required[str]
    template_data: Required[Mapping[str, Any]]


DirectConvertParams = DirectUrlParams | DirectHtmlParams | DirectTemplateParams


class SyncUrlParams(SyncOptions):
    url: Required[str]


class SyncHtmlParams(SyncOptions):
    html: Required[str]


class SyncTemplateParams(SyncOptions):
    template_id: Required[str]
    template_data: Required[Mapping[str, Any]]


SyncConvertParams = SyncUrlParams | SyncHtmlParams | SyncTemplateParams


class AsyncUrlParams(AsyncOptions):
    url: Required[str]
    webhook: Required[str]


class AsyncHtmlParams(AsyncOptions):
    html: Required[str]
    webhook: Required[str]


class AsyncTemplateParams(AsyncOptions):
    template_id: Required[str]
    template_data: Required[Mapping[str, Any]]
    webhook: Required[str]


AsyncConvertParams = AsyncUrlParams | AsyncHtmlParams | AsyncTemplateParams
