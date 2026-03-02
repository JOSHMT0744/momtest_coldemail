use crate::models::cold_companies::from_csv_record;
use axum::extract::Multipart;
use loco_rs::prelude::*;
use serde::Serialize;
use std::io::Cursor;

const CSV_FIELD_NAME: &str = "file";
const MAX_CSV_BYTES: usize = 50 * 1024 * 1024; // 50 MB

#[derive(Debug, Serialize)]
pub struct UploadResponse {
    pub inserted: u64,
    pub errors: Vec<String>,
}

/// POST /api/cold_companies/upload — accept multipart CSV and insert rows.
#[debug_handler]
async fn upload(State(ctx): State<AppContext>, mut multipart: Multipart) -> Result<Response> {
    let mut file_data: Option<Vec<u8>> = None;

    while let Some(mut field) = match multipart.next_field().await {
        Ok(opt) => opt,
        Err(e) => {
            tracing::warn!(error = %e, "multipart next_field error");
            return bad_request(e.to_string());
        }
    } {
        if field.name().as_deref() != Some(CSV_FIELD_NAME) {
            continue;
        }
        if let Some(name) = field.file_name() {
            if !name.ends_with(".csv") {
                return bad_request("Only .csv files are allowed");
            }
        }
        let mut bytes = Vec::new();
        while let Some(chunk) = match field.chunk().await {
            Ok(opt) => opt,
            Err(e) => {
                tracing::warn!(error = %e, "multipart chunk error");
                return bad_request(e.to_string());
            }
        } {
            if bytes.len() + chunk.len() > MAX_CSV_BYTES {
                return bad_request("File too large");
            }
            bytes.extend_from_slice(&chunk);
        }
        file_data = Some(bytes);
        break;
    }

    let data = match file_data {
        Some(d) => d,
        None => return bad_request("Missing file field (use field name 'file')"),
    };

    let cursor = Cursor::new(data);
    let mut reader = csv::Reader::from_reader(cursor);
    let headers: Vec<String> = match reader.headers() {
        Ok(h) => h.iter().map(|s| s.to_string()).collect(),
        Err(e) => {
            tracing::warn!(error = %e, "CSV headers error");
            return bad_request(format!("Invalid CSV headers: {}", e));
        }
    };

    let mut inserted: u64 = 0;
    let mut errors: Vec<String> = Vec::new();

    for (row_index, result) in reader.records().enumerate() {
        let record = match result {
            Ok(r) => r,
            Err(e) => {
                errors.push(format!("Row {}: parse error - {}", row_index + 2, e));
                continue;
            }
        };
        let values: Vec<String> = record.iter().map(|s| s.to_string()).collect();
        let active = from_csv_record(&headers, &values);
        match active.insert(&ctx.db).await {
            Ok(_) => inserted += 1,
            Err(e) => {
                errors.push(format!("Row {}: insert error - {}", row_index + 2, e));
            }
        }
    }

    format::json(UploadResponse { inserted, errors })
}

pub fn routes() -> Routes {
    Routes::new()
        .prefix("/api/cold_companies")
        .add("/upload", post(upload))
}
