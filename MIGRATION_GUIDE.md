# Database Integration - Migration Guide

## 📋 Overview

This guide helps you migrate from JSON-based storage to PostgreSQL database.

## 🎯 Migration Strategies

### Strategy 1: Fresh Start (Recommended for New Projects)

1. **Enable Database Mode**

   ```bash
   # In .env file
   USE_DATABASE=true
   DATABASE_URL=postgresql://user:pass@localhost:5432/dinero_ai
   ```

2. **Initialize Database**

   ```bash
   python database/init_db.py
   ```

3. **Start Using**
   - All new data goes to PostgreSQL
   - No migration needed

---

### Strategy 2: Migrate Existing Data

If you have existing JSON data in `memory/financial_history.json`:

1. **Create Migration Script**

   ```python
   # scripts/migrate_json_to_db.py
   import json
   from decimal import Decimal
   from database.connection import db_session
   from database.repositories import BusinessRepository, FinancialSnapshotRepository

   # Read JSON data
   with open('memory/financial_history.json', 'r') as f:
       history = json.load(f)

   # Create business (if not exists)
   with db_session() as session:
       biz_repo = BusinessRepository(session)
       business = biz_repo.create(
           business_name="My Business",
           gstin="29ABCDE1234F1Z5"  # Your GSTIN
       )
       business_id = business.id

   # Migrate snapshots
   with db_session() as session:
       snapshot_repo = FinancialSnapshotRepository(session)

       for entry in history:
           snapshot_repo.save_snapshot(
               business_id=business_id,
               month_label=entry['month'],
               revenue=Decimal(str(entry['revenue'])),
               expenses=Decimal(str(entry['expenses'])),
               profit=Decimal(str(entry['profit'])),
               receivables=Decimal(str(entry['receivables'])),
               profit_margin=Decimal(str(entry.get('profit_margin', 0))),
               health_score=entry.get('health_score', 0)
           )

   print(f"✅ Migrated {len(history)} snapshots")
   ```

2. **Run Migration**

   ```bash
   python scripts/migrate_json_to_db.py
   ```

3. **Verify**
   ```bash
   # Check database
   psql -U dinero_user -d dinero_ai -c "SELECT count(*) FROM financial_snapshots;"
   ```

---

### Strategy 3: Dual-Write (Safest for Production)

Run both JSON and Database simultaneously:

1. **Keep USE_DATABASE=false**

2. **Modify Code to Write to Both**

   ```python
   # In your code
   from utils.memory import save_memory as json_save
   from database.connection import db_session
   from database.repositories import FinancialSnapshotRepository

   def save_snapshot_dual(entry, business_id):
       # Save to JSON (existing)
       json_save(entry)

       # Also save to database
       try:
           with db_session() as session:
               repo = FinancialSnapshotRepository(session)
               repo.save_snapshot(business_id=business_id, **entry)
       except Exception as e:
           print(f"DB save failed: {e}")
           # Continue with JSON
   ```

3. **Monitor Both Systems**
   - Run for 1-2 weeks
   - Verify data consistency
   - Compare JSON vs DB queries

4. **Switch to DB Only**
   ```bash
   USE_DATABASE=true
   ```

---

## 🔄 Rollback Plan

If something goes wrong:

1. **Disable Database**

   ```bash
   USE_DATABASE=false
   ```

2. **App Falls Back to JSON**
   - No code changes needed
   - Existing JSON data still works

3. **Fix Issues**
   - Check database logs
   - Verify schema
   - Fix configuration

4. **Re-enable When Ready**
   ```bash
   USE_DATABASE=true
   ```

---

## 🧪 Testing Migration

Before production migration:

1. **Test with Sample Data**

   ```bash
   # Create test database
   createdb dinero_ai_test

   # Initialize
   DATABASE_URL=postgresql://user:pass@localhost/dinero_ai_test \
   python database/init_db.py

   # Test migration
   # ... run your migration script ...

   # Verify
   psql -d dinero_ai_test -c "SELECT * FROM financial_snapshots LIMIT 5;"
   ```

2. **Performance Testing**

   ```python
   import time

   # JSON mode
   start = time.time()
   history = load_memory()  # USE_DATABASE=false
   print(f"JSON: {time.time() - start}s")

   # DB mode
   start = time.time()
   history = load_memory()  # USE_DATABASE=true
   print(f"DB: {time.time() - start}s")
   ```

---

## 📊 Data Validation

After migration, verify:

```sql
-- Check snapshot count
SELECT COUNT(*) FROM financial_snapshots;

-- Check data integrity
SELECT
    month_label,
    revenue,
    expenses,
    profit,
    (revenue - expenses) as calculated_profit,
    (profit - (revenue - expenses)) as difference
FROM financial_snapshots
WHERE ABS(profit - (revenue - expenses)) > 0.01;

-- Check for duplicates
SELECT month_label, business_id, COUNT(*)
FROM financial_snapshots
GROUP BY month_label, business_id
HAVING COUNT(*) > 1;
```

---

## ⚠️ Common Issues

### Issue 1: Connection Failed

```
Error: could not connect to server
```

**Solution:**

```bash
# Check PostgreSQL is running
systemctl status postgresql  # Linux
brew services list            # Mac

# Check port
psql -U postgres -p 5432
```

### Issue 2: Schema Not Found

```
Error: relation "financial_snapshots" does not exist
```

**Solution:**

```bash
# Run schema initialization
python database/init_db.py --mode raw_sql
```

### Issue 3: UUID Import Error

```
Error: No module named 'uuid'
```

**Solution:**

```bash
# uuid is built-in, but ensure PostgreSQL extension
psql -d dinero_ai -c "CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";"
```

### Issue 4: Permission Denied

```
Error: permission denied for table
```

**Solution:**

```sql
-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE dinero_ai TO dinero_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO dinero_user;
```

---

## 📈 Performance Tips

1. **Connection Pooling**

   ```bash
   DB_POOL_SIZE=10
   DB_MAX_OVERFLOW=20
   ```

2. **Indexes**
   - Already included in schema
   - Monitor slow queries: `EXPLAIN ANALYZE SELECT ...`

3. **Batch Operations**

   ```python
   # Instead of individual inserts:
   with db_session() as session:
       for entry in entries:
           repo.save_snapshot(...)  # Multiple round trips

   # Use bulk operations:
   with db_session() as session:
       session.bulk_insert_mappings(FinancialSnapshot, entries)
   ```

---

## ✅ Post-Migration Checklist

- [ ] All historical data migrated
- [ ] Data integrity verified (profit = revenue - expenses)
- [ ] No duplicate entries
- [ ] Application connects successfully
- [ ] Queries return expected results
- [ ] Performance acceptable
- [ ] Backup created
- [ ] JSON files archived
- [ ] Monitoring in place

---

## 🆘 Support

If you encounter issues:

1. Check logs: `tail -f /var/log/postgresql/postgresql-15-main.log`
2. Enable SQL echo: `DB_ECHO=true`
3. Test connection: `python -c "from database.connection import db_health_check; print(db_health_check())"`
4. Rollback to JSON mode if critical

---

## 📚 Additional Resources

- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Alembic Migrations](https://alembic.sqlalchemy.org/)
