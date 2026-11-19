IF DB_ID('ideas') IS NULL CREATE DATABASE ideas;
GO
IF DB_ID('occasions') IS NULL CREATE DATABASE occasions;
GO

IF NOT EXISTS (SELECT 1 FROM sys.server_principals WHERE name = 'ideas_user')
    CREATE LOGIN ideas_user WITH PASSWORD = '$(IDEAS_PWD)';
GO
IF NOT EXISTS (SELECT 1 FROM sys.server_principals WHERE name = 'occasions_user')
    CREATE LOGIN occasions_user WITH PASSWORD = '$(OCCASIONS_PWD)';
GO

USE ideas;
GO
IF NOT EXISTS (SELECT 1 FROM sys.database_principals WHERE name = 'ideas_user')
    CREATE USER ideas_user FOR LOGIN ideas_user;
GO
ALTER ROLE db_owner ADD MEMBER ideas_user;
GO

USE occasions;
GO
IF NOT EXISTS (SELECT 1 FROM sys.database_principals WHERE name = 'occasions_user')
    CREATE USER occasions_user FOR LOGIN occasions_user;
GO
ALTER ROLE db_owner ADD MEMBER occasions_user;
GO
