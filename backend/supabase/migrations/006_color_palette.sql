-- Assign a color from the palette to a connected account
-- Colors cycle through a fixed palette per user
CREATE OR REPLACE FUNCTION public.assign_account_color(p_user_id UUID, p_account_id UUID)
RETURNS TEXT
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    palette TEXT[] := ARRAY[
        '#4F46E5', '#7C3AED', '#DB2777', '#DC2626',
        '#D97706', '#059669', '#0284C7', '#475569'
    ];
    account_count INT;
    chosen_color TEXT;
BEGIN
    SELECT COUNT(*) INTO account_count
    FROM public.connected_accounts
    WHERE user_id = p_user_id AND id != p_account_id;

    chosen_color := palette[(account_count % array_length(palette, 1)) + 1];

    UPDATE public.connected_accounts
    SET color = chosen_color
    WHERE id = p_account_id AND user_id = p_user_id;

    RETURN chosen_color;
END;
$$;
