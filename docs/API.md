# API guide

All farm endpoints use `Authorization: Bearer <access token>`.

| Capability | Endpoint |
|---|---|
| Crop prediction | `POST /api/v1/crop-predictions` |
| Fertilizer plan | `POST /api/v1/fertilizer-recommendations` |
| Weather | `POST /api/v1/weather` |
| Disease image | `POST /api/v1/disease-detections` multipart |
| Yield | `POST /api/v1/yield-predictions` |
| Soil health | `POST /api/v1/soil-health` |
| Irrigation | `POST /api/v1/irrigation-recommendations` |
| Market forecast | `POST /api/v1/market-price-predictions` |
| Chat | `POST /api/v1/chat` |
| Report export | `POST /api/v1/reports/{pdf|xlsx|csv}` |
| Admin users/analytics | `GET /api/v1/admin/users`, `GET /api/v1/admin/analytics` |

Interactive, request-schema documentation is served by FastAPI at `/docs`.
