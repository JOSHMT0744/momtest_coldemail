use loco_rs::prelude::*;
use sea_orm::ActiveValue;

pub use super::_entities::cold_companies::{ActiveModel, Entity, Model};

/// CSV header names (case-insensitive) mapped to our column names.
/// Headers from cro_united_kingdom_enriched.csv or common variants.
pub const CSV_HEADER_MAP: &[(&str, &str)] = &[
    ("vendor_name", "vendor_name"),
    ("vendor name", "vendor_name"),
    ("description", "description"),
    ("linkedin_url", "linkedin_url"),
    ("linkedin url", "linkedin_url"),
    ("linkedin_about_us", "linkedin_about_us"),
    ("linkedin about us", "linkedin_about_us"),
    ("linkedin_website", "linkedin_website"),
    ("linkedin website", "linkedin_website"),
    ("linkedin_phone", "linkedin_phone"),
    ("linkedin phone", "linkedin_phone"),
    ("linkedin_industry", "linkedin_industry"),
    ("linkedin industry", "linkedin_industry"),
    ("linkedin_company_type", "linkedin_company_type"),
    ("linkedin company type", "linkedin_company_type"),
    ("linkedin_company_size", "linkedin_company_size"),
    ("linkedin company size", "linkedin_company_size"),
    ("linkedin_specialties", "linkedin_specialties"),
    ("linkedin specialties", "linkedin_specialties"),
    ("linkedin_error", "linkedin_error"),
    ("linkedin error", "linkedin_error"),
];

fn csv_header_to_column(header: &str) -> Option<&'static str> {
    let normalized = header.trim().to_lowercase();
    CSV_HEADER_MAP
        .iter()
        .find(|(k, _)| k.to_lowercase() == normalized)
        .map(|(_, v)| *v)
}

/// Build an ActiveModel from a CSV record (row of string values) and header names.
/// Headers and record must have the same length; missing/extra columns yield None for unknown.
/// created_at/updated_at are left NotSet; create_table (Loco) adds them to the table and they are handled by the DB.
pub fn from_csv_record(headers: &[String], record: &[String]) -> ActiveModel {
    let mut model = ActiveModel {
        id: ActiveValue::NotSet,
        vendor_name: ActiveValue::Set(String::new()),
        description: ActiveValue::Set(None),
        linkedin_url: ActiveValue::Set(None),
        linkedin_about_us: ActiveValue::Set(None),
        linkedin_website: ActiveValue::Set(None),
        linkedin_phone: ActiveValue::Set(None),
        linkedin_industry: ActiveValue::Set(None),
        linkedin_company_type: ActiveValue::Set(None),
        linkedin_company_size: ActiveValue::Set(None),
        linkedin_specialties: ActiveValue::Set(None),
        linkedin_error: ActiveValue::Set(None),
        contacted: ActiveValue::Set(false),
        created_at: ActiveValue::NotSet,
        updated_at: ActiveValue::NotSet,
    };

    for (i, header) in headers.iter().enumerate() {
        let value = record.get(i).and_then(|s| {
            let t = s.trim();
            if t.is_empty() {
                None
            } else {
                Some(t.to_string())
            }
        });
        if let Some(col) = csv_header_to_column(header) {
            match col {
                "vendor_name" => model.vendor_name = ActiveValue::Set(value.unwrap_or_default()),
                "description" => model.description = ActiveValue::Set(value),
                "linkedin_url" => model.linkedin_url = ActiveValue::Set(value),
                "linkedin_about_us" => model.linkedin_about_us = ActiveValue::Set(value),
                "linkedin_website" => model.linkedin_website = ActiveValue::Set(value),
                "linkedin_phone" => model.linkedin_phone = ActiveValue::Set(value),
                "linkedin_industry" => model.linkedin_industry = ActiveValue::Set(value),
                "linkedin_company_type" => model.linkedin_company_type = ActiveValue::Set(value),
                "linkedin_company_size" => model.linkedin_company_size = ActiveValue::Set(value),
                "linkedin_specialties" => model.linkedin_specialties = ActiveValue::Set(value),
                "linkedin_error" => model.linkedin_error = ActiveValue::Set(value),
                _ => {}
            }
        }
    }
    model
}

/// Minimal impl so SeaORM is satisfied; created_at/updated_at are handled by the table (create_table).
#[async_trait::async_trait]
impl ActiveModelBehavior for super::_entities::cold_companies::ActiveModel {
    async fn before_save<C>(self, _db: &C, _insert: bool) -> Result<Self, DbErr>
    where
        C: sea_orm::ConnectionTrait,
    {
        Ok(self)
    }
}