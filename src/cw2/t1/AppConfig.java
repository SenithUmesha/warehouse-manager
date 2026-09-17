package cw2.t1;

/**
 * Runtime configuration for the historical desktop application.
 *
 * Values can be provided either as JVM system properties or environment
 * variables. No production credentials belong in the desktop source tree.
 */
public final class AppConfig {

    private AppConfig() {
    }

    private static String value(String property, String env, String fallback) {
        String systemValue = System.getProperty(property);
        if (systemValue != null && !systemValue.trim().isEmpty()) {
            return systemValue.trim();
        }

        String environmentValue = System.getenv(env);
        if (environmentValue != null && !environmentValue.trim().isEmpty()) {
            return environmentValue.trim();
        }

        return fallback;
    }

    public static String dbUrl() {
        return value("wms.db.url", "WMS_DB_URL", "jdbc:mysql://localhost:3306/wms");
    }

    public static String dbUser() {
        return value("wms.db.user", "WMS_DB_USER", "root");
    }

    public static String dbPassword() {
        return value("wms.db.password", "WMS_DB_PASSWORD", "");
    }

    public static String smtpUser() {
        return value("wms.smtp.user", "WMS_SMTP_USER", "");
    }

    public static String smtpPassword() {
        return value("wms.smtp.password", "WMS_SMTP_PASSWORD", "");
    }
}
