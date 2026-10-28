function total(items, tax = 0) {
  return items.reduce((s, x) => s + x.price, 0) * (1 + tax);
}

module.exports = { total };
