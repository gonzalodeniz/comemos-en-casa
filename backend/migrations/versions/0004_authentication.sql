-- Google OpenID Connect identities and opaque, server-side sessions.
-- State rows have no user/session bearer token; authenticated rows have both.

CREATE TABLE users (
    id uuid PRIMARY KEY,
    google_subject text NOT NULL UNIQUE,
    email text NOT NULL UNIQUE,
    display_name text NULL,
    picture_url text NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    CHECK (char_length(google_subject) BETWEEN 1 AND 255),
    CHECK (char_length(email) BETWEEN 3 AND 320),
    CHECK (email = lower(btrim(email))),
    CHECK (display_name IS NULL OR char_length(display_name) BETWEEN 1 AND 500),
    CHECK (picture_url IS NULL OR char_length(picture_url) BETWEEN 1 AND 2048)
);

CREATE TABLE auth_sessions (
    id uuid PRIMARY KEY,
    user_id uuid NULL REFERENCES users (id) ON DELETE CASCADE,
    session_token_hash char(64) NULL UNIQUE,
    state_hash char(64) NULL UNIQUE,
    oauth_nonce text NULL,
    expires_at timestamptz NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    last_seen_at timestamptz NULL,
    CHECK (
        (user_id IS NULL AND session_token_hash IS NULL AND state_hash IS NOT NULL AND oauth_nonce IS NOT NULL)
        OR
        (user_id IS NOT NULL AND session_token_hash IS NOT NULL AND state_hash IS NULL AND oauth_nonce IS NULL)
    )
);

CREATE INDEX auth_sessions_expiry_idx ON auth_sessions (expires_at);
CREATE INDEX auth_sessions_user_id_idx ON auth_sessions (user_id) WHERE user_id IS NOT NULL;
