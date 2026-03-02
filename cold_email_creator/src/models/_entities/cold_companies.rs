//! SeaORM entity for cold_companies table

use sea_orm::entity::prelude::*;
use serde::{Deserialize, Serialize};

#[derive(Clone, Debug, PartialEq, DeriveEntityModel, Eq, Serialize, Deserialize)]
#[sea_orm(table_name = "cold_companies")]
pub struct Model {
    #[sea_orm(primary_key)]
    pub id: i32,
    pub vendor_name: String,
    pub description: Option<String>,
    pub linkedin_url: Option<String>,
    pub linkedin_about_us: Option<String>,
    pub linkedin_website: Option<String>,
    pub linkedin_phone: Option<String>,
    pub linkedin_industry: Option<String>,
    pub linkedin_company_type: Option<String>,
    pub linkedin_company_size: Option<String>,
    pub linkedin_specialties: Option<String>,
    pub linkedin_error: Option<String>,
    pub contacted: bool,
    pub created_at: DateTimeWithTimeZone,
    pub updated_at: DateTimeWithTimeZone,
}

#[derive(Copy, Clone, Debug, EnumIter, DeriveRelation)]
pub enum Relation {}
