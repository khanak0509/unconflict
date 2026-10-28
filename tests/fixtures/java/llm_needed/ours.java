public class Price {
    public static int withTax(int cents) {
        return Math.round(cents * 1.10f);
    }
}
