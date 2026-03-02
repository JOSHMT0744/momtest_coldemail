use loco_rs::schema::*;
use sea_orm_migration::prelude::*;

#[derive(DeriveMigrationName)]
pub struct Migration;

#[async_trait::async_trait]
impl MigrationTrait for Migration {
    async fn up(&self, m: &SchemaManager) -> Result<(), DbErr> {
        create_table(
            m,
            "cold_companies",
            &[
                ("id", ColType::PkAuto),
                ("vendor_name", ColType::String),
                ("description", ColType::TextNull),
                ("linkedin_url", ColType::StringNull),
                ("linkedin_about_us", ColType::TextNull),
                ("linkedin_website", ColType::StringNull),
                ("linkedin_phone", ColType::StringNull),
                ("linkedin_industry", ColType::StringNull),
                ("linkedin_company_type", ColType::StringNull),
                ("linkedin_company_size", ColType::StringNull),
                ("linkedin_specialties", ColType::TextNull),
                ("linkedin_error", ColType::TextNull),
                ("contacted", ColType::BooleanWithDefault(false)),
            ],
            &[],
        )
        .await?;
        Ok(())
    }

    async fn down(&self, m: &SchemaManager) -> Result<(), DbErr> {
        drop_table(m, "cold_companies").await?;
        Ok(())
    }
}
