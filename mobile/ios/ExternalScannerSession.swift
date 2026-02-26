import Foundation

final class NotificationExternalScannerSession: ExternalScannerSession {
    static let defaultNotificationName = Notification.Name("AssetraExternalScan")

    private let center: NotificationCenter
    private let notificationName: Notification.Name
    private var observer: NSObjectProtocol?

    init(
        center: NotificationCenter = .default,
        notificationName: Notification.Name = NotificationExternalScannerSession.defaultNotificationName
    ) {
        self.center = center
        self.notificationName = notificationName
    }

    func start(onPayload: @escaping ([String: String]) -> Void) {
        stop()
        observer = center.addObserver(
            forName: notificationName,
            object: nil,
            queue: .main
        ) { notification in
            guard let userInfo = notification.userInfo else { return }
            let payload = userInfo.reduce(into: [String: String]()) { partial, item in
                partial[String(describing: item.key)] = String(describing: item.value)
            }
            if !payload.isEmpty {
                onPayload(payload)
            }
        }
    }

    func stop() {
        guard let observer else { return }
        center.removeObserver(observer)
        self.observer = nil
    }
}
