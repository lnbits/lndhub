window.PageLndhub = {
  template: '#page-lndhub',
  mixins: [windowMixin],
  data() {
    const mappedWallets = g.user.wallets.map(wallet => ({
      label: wallet.name,
      admin: `lndhub://admin:${wallet.adminkey}@${location.protocol}//${location.host}/lndhub/ext/`,
      invoice: `lndhub://invoice:${wallet.inkey}@${location.protocol}//${location.host}/lndhub/ext/`
    }))
    return {
      wallets: mappedWallets,
      selectedWallet: mappedWallets[0]
    }
  }
}
